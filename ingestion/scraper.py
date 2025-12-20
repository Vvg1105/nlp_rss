"""
Article scraper using RSS feeds and Newspaper3k
"""
import feedparser
from newspaper import Article
from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict, List, Optional
import logging
from .news_sources import NEWS_SOURCES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleScraper:
    """Scrapes articles from news sources using RSS feeds"""
    
    def __init__(self):
        self.sources = NEWS_SOURCES
    
    def fetch_rss_feed(self, feed_url: str) -> List[Dict]:
        """
        Fetch articles from an RSS feed
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            List of article metadata from the feed
        """
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries:
                article_data = {
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'published': entry.get('published', entry.get('updated', '')),
                    'summary': entry.get('summary', ''),
                }
                articles.append(article_data)
            
            logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            return articles
        
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    def extract_article_content(self, url: str, rss_metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Extract full article content using Newspaper3k
        
        Args:
            url: URL of the article
            rss_metadata: Optional metadata from RSS feed (contains publish date, title, etc.)
            
        Returns:
            Dictionary containing article content and metadata
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Use RSS publish date if newspaper3k couldn't extract it
            publish_date = article.publish_date
            if not publish_date and rss_metadata and rss_metadata.get('published'):
                try:
                    # Parse the RSS date string to datetime
                    publish_date = date_parser.parse(rss_metadata['published'])
                except Exception as e:
                    logger.warning(f"Could not parse date '{rss_metadata['published']}': {e}")
                    publish_date = None
            
            # Use RSS title as fallback if extraction failed
            title = article.title if article.title else (rss_metadata.get('title', '') if rss_metadata else '')
            
            return {
                'url': url,
                'title': title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': publish_date,
                'top_image': article.top_image,
            }
        
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None
    
    def scrape_source(self, source_key: str, max_articles: int = 10) -> List[Dict]:
        """
        Scrape articles from a specific news source
        
        Args:
            source_key: Key of the news source (e.g., 'bbc', 'cnn')
            max_articles: Maximum number of articles to scrape per feed
            
        Returns:
            List of scraped articles with full content
        """
        if source_key not in self.sources:
            logger.error(f"Unknown source: {source_key}")
            return []
        
        source = self.sources[source_key]
        all_articles = []
        
        logger.info(f"Scraping {source['name']}...")
        
        # Fetch articles from all RSS feeds for this source
        for feed_url in source['rss_feeds']:
            feed_articles = self.fetch_rss_feed(feed_url)
            
            # Limit articles per feed
            feed_articles = feed_articles[:max_articles]
            
            # Extract full content for each article
            for article_meta in feed_articles:
                full_article = self.extract_article_content(article_meta['url'], rss_metadata=article_meta)
                
                if full_article and full_article['text']:
                    # Add source information
                    full_article['source'] = source['name']
                    full_article['source_key'] = source_key
                    # Add RSS summary if available
                    full_article['rss_summary'] = article_meta.get('summary', '')
                    all_articles.append(full_article)
        
        logger.info(f"Successfully scraped {len(all_articles)} articles from {source['name']}")
        return all_articles
    
    def scrape_all_sources(self, max_articles_per_feed: int = 10) -> List[Dict]:
        """
        Scrape articles from all configured news sources
        
        Args:
            max_articles_per_feed: Maximum articles to scrape per RSS feed
            
        Returns:
            List of all scraped articles
        """
        all_articles = []
        
        for source_key in self.sources.keys():
            articles = self.scrape_source(source_key, max_articles_per_feed)
            all_articles.extend(articles)
        
        logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles


# Example usage
if __name__ == "__main__":
    scraper = ArticleScraper()
    
    # Example 1: Scrape a single source (BBC)
    print("\n=== Scraping BBC News ===")
    bbc_articles = scraper.scrape_source('bbc', max_articles=3)
    
    if bbc_articles:
        article = bbc_articles[0]
        print(f"\nTitle: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"URL: {article['url']}")
        print(f"Published: {article['publish_date']}")
        print(f"Text preview: {article['text'][:200]}...")
    
    # Example 2: Scrape all sources
    print("\n\n=== Scraping All Sources ===")
    all_articles = scraper.scrape_all_sources(max_articles_per_feed=2)
    
    print(f"\nTotal articles: {len(all_articles)}")
    print("\nArticles by source:")
    
    # Count articles by source
    source_counts = {}
    for article in all_articles:
        source = article['source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in source_counts.items():
        print(f"  {source}: {count} articles")

