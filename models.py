# Legacy compatibility bridge for existing imports
# This file maintains backward compatibility while redirecting to the new structure

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new structure
from src.models.todo import TodoItem
from src.models.event import EventItem
from src.models.database import db_manager

# Legacy function compatibility
def get_db():
    """Legacy compatibility function"""
    return db_manager.get_session()

# Export for backward compatibility
__all__ = ['TodoItem', 'EventItem', 'get_db']
