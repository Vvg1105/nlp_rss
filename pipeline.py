"""
Complete News Article Pipeline
Scrape → Save → Embed → Cluster

This is the main orchestrator that runs the entire pipeline end-to-end.
"""
from ingestion.scraper import ArticleScraper
from ingestion.article_storage import save_articles
from ingestion.embedding_vector_algo import generate_embedding_vector
from backend.clustering import cluster_articles
from backend.database import SessionLocal
from backend.models.article_table import Article
import time


def step1_scrape_articles(sources=None, max_articles_per_feed=10):
    """
    Step 1: Scrape articles from news sources
    
    Args:
        sources: List of source keys (e.g., ['bbc', 'guardian']) or None for all
        max_articles_per_feed: Number of articles per RSS feed
        
    Returns:
        List of scraped articles
    """
    print("=" * 60)
    print("STEP 1: SCRAPING ARTICLES")
    print("=" * 60)
    
    scraper = ArticleScraper()
    
    if sources:
        # Scrape specific sources
        all_articles = []
        for source in sources:
            print(f"\nScraping {source}...")
            articles = scraper.scrape_source(source, max_articles=max_articles_per_feed)
            all_articles.extend(articles)
    else:
        # Scrape all sources
        all_articles = scraper.scrape_all_sources(max_articles_per_feed=max_articles_per_feed)
    
    print(f"\n✅ Scraped {len(all_articles)} total articles")
    return all_articles


def step2_save_to_database(articles):
    """
    Step 2: Save articles to database
    
    Args:
        articles: List of article dictionaries from scraper
        
    Returns:
        Number of articles saved
    """
    print("\n" + "=" * 60)
    print("STEP 2: SAVING TO DATABASE")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        count = save_articles(articles, db)
        print(f"\n✅ Saved {count} new articles to database")
        return count
    finally:
        db.close()


def step3_generate_embeddings():
    """
    Step 3: Generate embeddings for articles without them
    
    Returns:
        Number of embeddings generated
    """
    print("\n" + "=" * 60)
    print("STEP 3: GENERATING EMBEDDINGS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Find articles without embeddings
        articles_without_embeddings = db.query(Article).filter(
            Article.embedding_vector == None
        ).all()
        
        print(f"Found {len(articles_without_embeddings)} articles without embeddings")
        
        if len(articles_without_embeddings) == 0:
            print("No articles to process!")
            return 0
        
        # Generate embeddings
        for i, article in enumerate(articles_without_embeddings, 1):
            print(f"Processing {i}/{len(articles_without_embeddings)}: {article.title[:60]}...")
            
            # Generate embedding from title
            embedding_str = generate_embedding_vector(article.title)
            article.embedding_vector = embedding_str
        
        # Commit all at once
        db.commit()
        print(f"\n✅ Generated {len(articles_without_embeddings)} embeddings")
        return len(articles_without_embeddings)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def step4_cluster_into_events(threshold=0.75):
    """
    Step 4: Cluster articles into events
    
    Args:
        threshold: Similarity threshold for clustering (default 0.75)
        
    Returns:
        Clustering statistics
    """
    print("\n" + "=" * 60)
    print("STEP 4: CLUSTERING INTO EVENTS")
    print("=" * 60)
    
    stats = cluster_articles(threshold=threshold)
    print(f"\n✅ Clustering complete")
    return stats


def run_complete_pipeline(sources=None, max_articles_per_feed=10, threshold=0.75):
    """
    Run the complete end-to-end pipeline
    
    Args:
        sources: List of news sources to scrape (None = all)
        max_articles_per_feed: Articles to scrape per RSS feed
        threshold: Clustering similarity threshold
        
    Returns:
        Dictionary with pipeline statistics
    """
    start_time = time.time()
    
    print("\n" + "🚀" * 30)
    print("STARTING COMPLETE NEWS PIPELINE")
    print("🚀" * 30)
    
    # Step 1: Scrape
    articles = step1_scrape_articles(sources, max_articles_per_feed)
    
    # Step 2: Save
    saved_count = step2_save_to_database(articles)
    
    # Step 3: Generate embeddings
    embeddings_count = step3_generate_embeddings()
    
    # Step 4: Cluster
    cluster_stats = step4_cluster_into_events(threshold)
    
    # Summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE! 🎉")
    print("=" * 60)
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"\nSummary:")
    print(f"  Articles scraped: {len(articles)}")
    print(f"  Articles saved (new): {saved_count}")
    print(f"  Embeddings generated: {embeddings_count}")
    print(f"  Events created: {cluster_stats['new_events_created']}")
    print(f"  Articles assigned to existing events: {cluster_stats['assigned_to_existing']}")
    
    return {
        'scraped': len(articles),
        'saved': saved_count,
        'embeddings': embeddings_count,
        'clustering': cluster_stats,
        'time_seconds': elapsed_time
    }


def run_incremental_update(sources=None, max_articles_per_feed=5, threshold=0.75):
    """
    Run an incremental update (for scheduled runs)
    Same as complete pipeline but with fewer articles
    
    Args:
        sources: List of news sources to scrape (None = all)
        max_articles_per_feed: Articles to scrape per RSS feed (default 5 for incremental)
        threshold: Clustering similarity threshold
    """
    return run_complete_pipeline(sources, max_articles_per_feed, threshold)


if __name__ == "__main__":
    # Test the complete pipeline with just Guardian articles
    print("Testing pipeline with Guardian articles...")
    
    results = run_complete_pipeline(
        sources=['guardian'],  # Just Guardian for testing
        max_articles_per_feed=5,  # Only 5 articles for quick test
        threshold=0.75
    )
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print("\nTo run the full pipeline on all sources:")
    print("  python pipeline.py")
    print("\nTo run incrementally:")
    print("  from pipeline import run_incremental_update")
    print("  run_incremental_update(max_articles_per_feed=5)")

