from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from src.config import settings
from src.core import logger, DatabaseException

Base = declarative_base()

class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Database initialized with URL: {self.database_url}")
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with proper cleanup"""
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise DatabaseException(f"Database operation failed: {str(e)}")
        finally:
            db.close()
    
    @contextmanager
    def get_session_context(self) -> Session:
        """Get database session as context manager"""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise DatabaseException(f"Database operation failed: {str(e)}")
        finally:
            db.close()

db_manager = DatabaseManager()