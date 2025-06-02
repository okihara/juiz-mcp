from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .database import Base

class TodoItem(Base):
    """Database model for TODO items"""
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class TodoItemSchema(BaseModel):
    """Pydantic schema for TODO items"""
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

class TodoCreateSchema(BaseModel):
    """Schema for creating TODO items"""
    user_id: str
    title: str
    description: Optional[str] = None

class TodoUpdateSchema(BaseModel):
    """Schema for updating TODO items"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None