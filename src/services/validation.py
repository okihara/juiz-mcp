from typing import Any, Dict
from datetime import datetime
from src.core import ValidationException

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_user_id(user_id: str) -> str:
        """Validate user ID"""
        if not user_id or not isinstance(user_id, str):
            raise ValidationException("User ID must be a non-empty string")
        if len(user_id.strip()) == 0:
            raise ValidationException("User ID cannot be empty")
        return user_id.strip()
    
    @staticmethod
    def validate_title(title: str) -> str:
        """Validate title"""
        if not title or not isinstance(title, str):
            raise ValidationException("Title must be a non-empty string")
        if len(title.strip()) == 0:
            raise ValidationException("Title cannot be empty")
        if len(title.strip()) > 200:
            raise ValidationException("Title cannot exceed 200 characters")
        return title.strip()
    
    @staticmethod
    def validate_description(description: str = None) -> str:
        """Validate description"""
        if description is None:
            return None
        if not isinstance(description, str):
            raise ValidationException("Description must be a string")
        if len(description.strip()) > 1000:
            raise ValidationException("Description cannot exceed 1000 characters")
        return description.strip() if description.strip() else None
    
    @staticmethod
    def validate_datetime(dt: datetime, field_name: str) -> datetime:
        """Validate datetime"""
        if not isinstance(dt, datetime):
            raise ValidationException(f"{field_name} must be a valid datetime")
        return dt
    
    @staticmethod
    def validate_event_times(start_time: datetime, end_time: datetime) -> None:
        """Validate event start/end times"""
        if start_time >= end_time:
            raise ValidationException("End time must be after start time")
    
    @staticmethod
    def validate_filter_status(filter_status: str) -> str:
        """Validate filter status"""
        valid_statuses = ["all", "completed", "active"]
        if filter_status not in valid_statuses:
            raise ValidationException(f"Invalid filter status: {filter_status}. Use 'all', 'completed', or 'active'.")
        return filter_status