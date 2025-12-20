from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Article(Base):
    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    url = Column(String, index=True)
    title = Column(String, index=True)
    published_at_time = Column(DateTime, index=True)
    full_text = Column(String, index=True)
    embedding_vector = Column(String, index=True)
    event_id = Column(Integer, ForeignKey("events.event_id"), index=True, default = None) 