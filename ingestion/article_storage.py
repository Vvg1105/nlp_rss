from backend.models.article_table import Article
from backend.database import SessionLocal
from sqlalchemy.orm import Session

def save_articles(articles_list, db_session: Session):
    """
    Save a list of article dictionaries to the database
    
    Args:
        articles_list: List of article dicts from scraper
        db_session: SQLAlchemy session
    
    Returns:
        Number of new articles saved
    """
    saved_count = 0
    
    try:
        for article_dict in articles_list:
            # Check if article already exists (by URL) - efficient query
            existing = db_session.query(Article).filter(
                Article.url == article_dict['url']
            ).first()
            
            if not existing:
                # Create new article object
                new_article = Article(
                    source=article_dict['source'],
                    url=article_dict['url'],
                    title=article_dict['title'],
                    published_at_time=article_dict['publish_date'],
                    full_text=article_dict['text'],
                    embedding_vector=None,  # Generate in separate step
                    event_id=None  # Will be assigned during clustering
                )
                
                db_session.add(new_article)
                saved_count += 1
            else:
                print(f"Article already exists: {article_dict['url']}")
        
        # Commit all at once
        db_session.commit()
        print(f"Saved {saved_count} new articles to the database")
        return saved_count
        
    except Exception as e:
        print(f"Error saving articles: {e}")
        db_session.rollback()
        raise
