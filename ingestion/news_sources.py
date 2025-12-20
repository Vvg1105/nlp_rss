"""
News source configurations with RSS feeds
"""

NEWS_SOURCES = {
    "bbc": {
        "name": "BBC News",
        "rss_feeds": [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/business/rss.xml",
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
        ],
        "base_url": "https://www.bbc.com"
    },
    "reuters": {
        "name": "Reuters",
        "rss_feeds": [
            "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        ],
        "base_url": "https://www.reuters.com"
    },
    "cnn": {
        "name": "CNN",
        "rss_feeds": [
            "http://rss.cnn.com/rss/cnn_topstories.rss",
            "http://rss.cnn.com/rss/cnn_world.rss",
            "http://rss.cnn.com/rss/cnn_tech.rss",
        ],
        "base_url": "https://www.cnn.com"
    },
    "guardian": {
        "name": "The Guardian",
        "rss_feeds": [
            "https://www.theguardian.com/world/rss",
            "https://www.theguardian.com/uk/technology/rss",
            "https://www.theguardian.com/business/rss",
        ],
        "base_url": "https://www.theguardian.com"
    }
}

