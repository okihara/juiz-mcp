from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import EventItem, EventItemSchema, EventCreateSchema, db_manager
from src.core import logger, NotFoundError, PermissionError, ResponseFormatter, ValidationException
from .validation import Validator

class EventService:
    """Service layer for Event operations"""
    
    def __init__(self):
        self.validator = Validator()
    
    def create_event(self, user_id: str, title: str, start_time: datetime, 
                    end_time: datetime, description: str = None, location: str = None) -> Dict:
        """Create a new event item"""
        try:
            # Validate inputs
            user_id = self.validator.validate_user_id(user_id)
            title = self.validator.validate_title(title)
            description = self.validator.validate_description(description)
            start_time = self.validator.validate_datetime(start_time, "start_time")
            end_time = self.validator.validate_datetime(end_time, "end_time")
            self.validator.validate_event_times(start_time, end_time)
            
            # Validate location
            if location:
                if len(location.strip()) > 200:
                    raise ValidationException("Location cannot exceed 200 characters")
                location = location.strip()
            
            # Create Event
            with db_manager.get_session_context() as db:
                db_event = EventItem(
                    user_id=user_id,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    created_at=datetime.now()
                )
                
                db.add(db_event)
                db.flush()  # Get the ID before commit
                db.refresh(db_event)
                
                event_data = EventItemSchema.from_orm(db_event).dict()
                
            logger.info(f"Created Event {db_event.id} for user {user_id}")
            return ResponseFormatter.success(event_data)
            
        except Exception as e:
            logger.error(f"Error creating Event: {str(e)}")
            return ResponseFormatter.from_exception(e)
    
    def get_event(self, user_id: str, event_id: int) -> Dict:
        """Get a specific event item"""
        try:
            user_id = self.validator.validate_user_id(user_id)
            
            with db_manager.get_session_context() as db:
                event = db.query(EventItem).filter(EventItem.id == event_id).first()
                
                if event is None:
                    raise NotFoundError(f"Event with ID {event_id} not found")
                
                if event.user_id != user_id:
                    raise PermissionError(f"Event with ID {event_id} not found for user {user_id}")
                
                event_data = EventItemSchema.from_orm(event).dict()
                
            return ResponseFormatter.success(event_data)
            
        except Exception as e:
            logger.error(f"Error getting Event {event_id}: {str(e)}")
            return ResponseFormatter.from_exception(e)
    
    def get_all_events(self, user_id: str, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> Dict:
        """Get all event items for a user"""
        try:
            user_id = self.validator.validate_user_id(user_id)
            
            if start_date:
                start_date = self.validator.validate_datetime(start_date, "start_date")
            if end_date:
                end_date = self.validator.validate_datetime(end_date, "end_date")
            
            with db_manager.get_session_context() as db:
                query = db.query(EventItem).filter(EventItem.user_id == user_id)
                
                # Apply date filters
                if start_date:
                    query = query.filter(EventItem.start_time >= start_date)
                if end_date:
                    query = query.filter(EventItem.end_time <= end_date)
                
                # Order by start time
                query = query.order_by(EventItem.start_time)
                
                events = query.all()
                events_data = [EventItemSchema.from_orm(event).dict() for event in events]
                
            logger.info(f"Retrieved {len(events_data)} Events for user {user_id}")
            return ResponseFormatter.success(events_data)
            
        except Exception as e:
            logger.error(f"Error getting Events for user {user_id}: {str(e)}")
            return ResponseFormatter.from_exception(e)