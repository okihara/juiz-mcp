from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GoogleCredentials(BaseModel):
    id: int
    user_id: str
    token_json: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True