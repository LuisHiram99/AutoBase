import logging
from logging.handlers import RotatingFileHandler
import sys
import os


def setup_logging():
    """
    Setup logging configuration for the application.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    os.makedirs("logs", exist_ok=True)
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler with rotation
            RotatingFileHandler(
                "logs/app.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    # Configure uvicorn logger
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.setLevel(logging.INFO)

    return logging.getLogger("app_logger")

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    """
    return logging.getLogger(name)