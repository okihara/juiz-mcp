from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TodoItem(BaseModel):
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


class EventItem(BaseModel):
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


class GoogleCredentials(BaseModel):
    id: int
    user_id: str
    token_json: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True