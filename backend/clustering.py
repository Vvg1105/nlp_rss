from sqlalchemy.orm import Session
from backend.models.event_table import Event
from backend.database import SessionLocal
from backend.models.article_table import Article
import json
import numpy as np
from sentence_transformers import util


def find_best_matching_event(article_embedding, threshold=0.75, db_session: Session = None):
    """ 
    Find the best matching event for a given article embedding
    
    Args:
        article_embedding: List of floats (parsed embedding)
        threshold: Minimum similarity score
        db_session: Database session
        
    Returns:
        (event_id, similarity_score) if match found, else None
    """
    if db_session is None:
        db_session = SessionLocal()

    events_in_db = db_session.query(Event).all()
    best_match = None
    best_match_score = -1

    for event in events_in_db:
        if event.centroid_embedding is not None:
            # Parse the centroid embedding from JSON string
            event_embedding = json.loads(event.centroid_embedding)
            
            # Calculate cosine similarity and extract scalar value
            result = util.cos_sim(article_embedding, event_embedding).item()

            if result > threshold and result > best_match_score:
                best_match = event.event_id
                best_match_score = result
    
    if best_match is None:
        return None
    
    return best_match, best_match_score


def update_event_centroid(event_id, db_session: Session):
    """
    Recalculate event centroid from all its articles
    
    Args:
        event_id: ID of event to update
        db_session: Database session
    """
    # Get all articles in this event
    articles = db_session.query(Article).filter(Article.event_id == event_id).all()
    
    # Parse all embeddings
    embeddings = []
    for article in articles:
        if article.embedding_vector:
            embeddings.append(json.loads(article.embedding_vector))
    
    if not embeddings:
        print(f"Warning: No embeddings found for event {event_id}")
        return
    
    # Calculate average (centroid)
    centroid = np.mean(embeddings, axis=0).tolist()
    
    # Update event
    event = db_session.query(Event).filter(Event.event_id == event_id).first()
    event.centroid_embedding = json.dumps(centroid)
    event.article_count = len(articles)
    
    # Update start_time and last_update
    article_times = [a.published_at_time for a in articles if a.published_at_time]
    if article_times:
        event.start_time = min(article_times)
        event.last_update = max(article_times)
    
    db_session.commit()
    print(f"Updated event {event_id} centroid: {len(articles)} articles")


def create_new_event_from_article(article, db_session: Session):
    """
    Create a new event from an article
    
    Args:
        article: Article object
        db_session: Database session
        
    Returns:
        New Event object
    """
    # Create new event with article as first member
    new_event = Event(
        title=article.title,
        summary="",  
        start_time=article.published_at_time,
        last_update=article.published_at_time,
        centroid_embedding=article.embedding_vector,
        article_count=1
    )
    
    db_session.add(new_event)
    db_session.commit()
    
    # Assign article to this new event
    article.event_id = new_event.event_id
    db_session.commit()
    
    print(f"Created new event {new_event.event_id}: {article.title[:60]}")
    return new_event


def cluster_articles(threshold=0.75, db_session: Session = None):
    """
    Cluster all unassigned articles into events
    
    Args:
        threshold: Similarity threshold for matching (default 0.75)
        db_session: Database session
        
    Returns:
        Dict with statistics
    """
    if db_session is None:
        db_session = SessionLocal()

    # Get articles without event assignment and with embeddings
    articles_to_cluster = db_session.query(Article).filter(
        Article.event_id == None,
        Article.embedding_vector != None
    ).all()
    
    print(f"Found {len(articles_to_cluster)} articles to cluster")
    
    new_events_created = 0
    articles_assigned = 0
    
    for i, article in enumerate(articles_to_cluster, 1):
        print(f"\nProcessing article {i}/{len(articles_to_cluster)}: {article.title[:60]}")
        
        # Parse article embedding
        article_embedding = json.loads(article.embedding_vector)
        
        # Try to find matching event
        match_result = find_best_matching_event(article_embedding, threshold, db_session)
        
        if match_result:
            # Found a match - assign to existing event
            match, score = match_result
            article.event_id = match
            db_session.commit()
            
            # Update event centroid
            update_event_centroid(match, db_session)
            
            articles_assigned += 1
            print(f"Assigned to event {match} (similarity: {score:.3f})")
        else:
            # No match - create new event
            create_new_event_from_article(article, db_session)
            new_events_created += 1
    
    stats = {
        'total_processed': len(articles_to_cluster),
        'assigned_to_existing': articles_assigned,
        'new_events_created': new_events_created
    }
    
    print(f"\nClustering complete!")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Assigned to existing events: {stats['assigned_to_existing']}")
    print(f"New events created: {stats['new_events_created']}")
    
    return stats


if __name__ == "__main__":
    # Test clustering
    cluster_articles(threshold=0.75)
