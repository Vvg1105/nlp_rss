"""
News Article Pipeline DAG for Apache Airflow

This DAG orchestrates the complete news scraping, embedding, and clustering pipeline.
Schedule: Runs every hour to fetch fresh news articles.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
# DAG is in airflow/dags/, so go up 2 levels to reach project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.scraper import ArticleScraper
from ingestion.article_storage import save_articles
from ingestion.embedding_vector_algo import generate_embedding_vector
from backend.clustering import cluster_articles
from backend.database import SessionLocal
from backend.models.article_table import Article


# Default arguments for the DAG
default_args = {
    'owner': 'nlp_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,  # Retry failed tasks twice
    'retry_delay': timedelta(minutes=5),  # Wait 5 min between retries
}


def scrape_articles_task(**context):
    """
    Task 1: Scrape articles from news sources
    """
    print("🔍 Starting article scraping...")
    
    # Get max articles from Airflow Variable
    max_articles = int(Variable.get("max_articles_per_feed", default_var=10))
    print(f"Max articles per feed: {max_articles}")
    
    scraper = ArticleScraper()
    articles = scraper.scrape_all_sources(max_articles_per_feed=max_articles)
    
    print(f"✅ Scraped {len(articles)} articles")
    
    # Push to XCom so next task can access
    context['ti'].xcom_push(key='scraped_articles', value=articles)
    return len(articles)


def save_articles_task(**context):
    """
    Task 2: Save scraped articles to database
    """
    print("💾 Starting article save...")
    
    # Pull articles from previous task
    articles = context['ti'].xcom_pull(key='scraped_articles', task_ids='scrape_articles')
    
    if not articles:
        print("⚠️ No articles to save")
        return 0
    
    db = SessionLocal()
    try:
        count = save_articles(articles, db)
        print(f"✅ Saved {count} new articles")
        return count
    finally:
        db.close()


def generate_embeddings_task(**context):
    """
    Task 3: Generate embeddings for articles without them
    """
    print("🧠 Starting embedding generation...")
    
    db = SessionLocal()
    try:
        # Find articles without embeddings
        articles_without_embeddings = db.query(Article).filter(
            Article.embedding_vector == None
        ).all()
        
        print(f"Found {len(articles_without_embeddings)} articles without embeddings")
        
        if len(articles_without_embeddings) == 0:
            return 0
        
        # Generate embeddings
        for i, article in enumerate(articles_without_embeddings, 1):
            print(f"Processing {i}/{len(articles_without_embeddings)}: {article.title[:60]}...")
            embedding_str = generate_embedding_vector(article.title)
            article.embedding_vector = embedding_str
        
        db.commit()
        print(f"✅ Generated {len(articles_without_embeddings)} embeddings")
        return len(articles_without_embeddings)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def cluster_articles_task(**context):
    """
    Task 4: Cluster articles into events
    """
    print("🔗 Starting article clustering...")
    
    # Get clustering threshold from Airflow Variable
    threshold = float(Variable.get("clustering_threshold", default_var=0.75))
    print(f"Using clustering threshold: {threshold}")
    
    stats = cluster_articles(threshold=threshold)
    
    print(f"✅ Clustering complete:")
    print(f"   New events: {stats['new_events_created']}")
    print(f"   Articles assigned: {stats['assigned_to_existing']}")
    
    return stats


# Define the DAG
with DAG(
    dag_id='news_article_pipeline',
    default_args=default_args,
    description='Scrape, embed, and cluster news articles',
    schedule='@hourly',  # Run every hour
    start_date=datetime(2025, 12, 20),
    catchup=False,  # Don't backfill past runs
    tags=['news', 'nlp', 'clustering'],
) as dag:
    
    # Task 1: Scrape articles
    scrape_task = PythonOperator(
        task_id='scrape_articles',
        python_callable=scrape_articles_task,
    )
    
    # Task 2: Save to database
    save_task = PythonOperator(
        task_id='save_articles',
        python_callable=save_articles_task,
    )
    
    # Task 3: Generate embeddings
    embed_task = PythonOperator(
        task_id='generate_embeddings',
        python_callable=generate_embeddings_task,
    )
    
    # Task 4: Cluster into events
    cluster_task = PythonOperator(
        task_id='cluster_articles',
        python_callable=cluster_articles_task,
    )
    
    # Define task dependencies (DAG structure)
    scrape_task >> save_task >> embed_task >> cluster_task

