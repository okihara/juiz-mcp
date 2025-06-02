from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import TodoItem, TodoItemSchema, TodoCreateSchema, TodoUpdateSchema, db_manager
from src.core import logger, NotFoundError, PermissionError, ResponseFormatter
from .validation import Validator

class TodoService:
    """Service layer for TODO operations"""
    
    def __init__(self):
        self.validator = Validator()
    
    def create_todo(self, user_id: str, title: str, description: str = None) -> Dict:
        """Create a new TODO item"""
        try:
            # Validate inputs
            user_id = self.validator.validate_user_id(user_id)
            title = self.validator.validate_title(title)
            description = self.validator.validate_description(description)
            
            # Create TODO
            with db_manager.get_session_context() as db:
                db_todo = TodoItem(
                    user_id=user_id,
                    title=title,
                    description=description,
                    created_at=datetime.now()
                )
                
                db.add(db_todo)
                db.flush()  # Get the ID before commit
                db.refresh(db_todo)
                
                todo_data = TodoItemSchema.from_orm(db_todo).dict()
                
            logger.info(f"Created TODO {db_todo.id} for user {user_id}")
            return ResponseFormatter.success(todo_data)
            
        except Exception as e:
            logger.error(f"Error creating TODO: {str(e)}")
            return ResponseFormatter.from_exception(e)
    
    def get_todo(self, user_id: str, todo_id: int) -> Dict:
        """Get a specific TODO item"""
        try:
            user_id = self.validator.validate_user_id(user_id)
            
            with db_manager.get_session_context() as db:
                todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
                
                if todo is None:
                    raise NotFoundError(f"Todo with ID {todo_id} not found")
                
                if todo.user_id != user_id:
                    raise PermissionError(f"Todo with ID {todo_id} not found for user {user_id}")
                
                todo_data = TodoItemSchema.from_orm(todo).dict()
                
            return ResponseFormatter.success(todo_data)
            
        except Exception as e:
            logger.error(f"Error getting TODO {todo_id}: {str(e)}")
            return ResponseFormatter.from_exception(e)
    
    def get_all_todos(self, user_id: str, filter_status: str = "all") -> Dict:
        """Get all TODO items for a user"""
        try:
            user_id = self.validator.validate_user_id(user_id)
            filter_status = self.validator.validate_filter_status(filter_status)
            
            with db_manager.get_session_context() as db:
                query = db.query(TodoItem).filter(TodoItem.user_id == user_id)
                
                # Apply filter
                if filter_status == "completed":
                    query = query.filter(TodoItem.completed == True)
                elif filter_status == "active":
                    query = query.filter(TodoItem.completed == False)
                
                todos = query.all()
                todos_data = [TodoItemSchema.from_orm(todo).dict() for todo in todos]
                
            logger.info(f"Retrieved {len(todos_data)} TODOs for user {user_id} with filter {filter_status}")
            return ResponseFormatter.success(todos_data)
            
        except Exception as e:
            logger.error(f"Error getting TODOs for user {user_id}: {str(e)}")
            return ResponseFormatter.from_exception(e)
    
    def update_todo_status(self, user_id: str, todo_id: int, completed: bool) -> Dict:
        """Update TODO completion status"""
        try:
            user_id = self.validator.validate_user_id(user_id)
            
            with db_manager.get_session_context() as db:
                todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
                
                if todo is None:
                    raise NotFoundError(f"Todo with ID {todo_id} not found")
                
                if todo.user_id != user_id:
                    raise PermissionError(f"Todo with ID {todo_id} not found for user {user_id}")
                
                todo.completed = completed
                db.flush()
                db.refresh(todo)
                
                todo_data = TodoItemSchema.from_orm(todo).dict()
                
            logger.info(f"Updated TODO {todo_id} status to {completed} for user {user_id}")
            return ResponseFormatter.success(todo_data)
            
        except Exception as e:
            logger.error(f"Error updating TODO {todo_id}: {str(e)}")
            return ResponseFormatter.from_exception(e)