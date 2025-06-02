from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        if not self.database_url:
            self.database_url = "sqlite:///./test.db"
        
        self.port: int = int(os.getenv("PORT", 8000))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()