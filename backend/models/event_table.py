from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    summary = Column(String, index=True)
    start_time = Column(DateTime, index=True)
    last_update = Column(DateTime, index=True)
    centroid_embedding = Column(String, index=True)
    article_count = Column(Integer, index=True)

