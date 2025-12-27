import sys
import os
from loguru import logger
from logtail import LogtailHandler
from pathlib import Path
from dotenv import load_dotenv
 
# Load environment variables from config/.env
try:
    # In Docker, config is at /app/config/.env
    # For local dev, it's at backend/config/.env relative to repo root
    env_path = Path('/app/config/.env')
    if not env_path.exists():
        # Fallback for local development
        # Go up 2 levels: logger -> src -> backend, then add config/.env
        env_path = Path(__file__).resolve().parents[2] / 'config' / '.env'
    load_dotenv(dotenv_path=env_path)
except Exception as e:
    print(f"Error loading .env file: {e}", file=sys.stderr)

environment = os.getenv("ENVIRONMENT", "development").lower()
log_level = "DEBUG" if environment == "development" else "INFO"
logs_source_token = os.getenv("LOGS_SOURCE_TOKEN", "")

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure Loguru logger
logger.remove()

logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=log_level
)
logger.add(
    str(logs_dir / "app.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=log_level,
    rotation="10 seconds",
    retention="5 seconds"
)

if logs_source_token:
    handler = LogtailHandler(source_token=logs_source_token, host=os.getenv("LOGS_SOURCE_HOST"))
    logger.add(
        handler,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        serialize=True
    )



logger.debug(f"Logger initialized in {environment} mode with level {log_level}")

def get_logger():
    return logger