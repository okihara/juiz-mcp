import logging
import sys
from typing import Optional
from src.config import settings

def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    log_level = level or settings.log_level
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("juiz-mcp")
    return logger

logger = setup_logging()