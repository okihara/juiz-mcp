from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .database import Base

class EventItem(Base):
    """Database model for event items"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class EventItemSchema(BaseModel):
    """Pydantic schema for event items"""
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

class EventCreateSchema(BaseModel):
    """Schema for creating event items"""
    user_id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None