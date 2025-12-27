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
    
    print(f"Looking for .env file at: {env_path}")
    print(f".env file exists: {env_path.exists()}")
    load_dotenv(dotenv_path=env_path)
except Exception as e:
    print(f"Error loading .env file: {e}", file=sys.stderr)

environment = os.getenv("ENVIRONMENT", "development").lower()
log_level = "DEBUG" if environment == "development" else "INFO"
logs_source_token = os.getenv("LOGS_SOURCE_TOKEN", "")
handler = LogtailHandler(source_token=str(logs_source_token), host="s1653917.eu-nbg-2.betterstackdata.com")

print(f"LOGS_SOURCE_TOKEN: {logs_source_token}")

# Configure Loguru logger
logger.remove()

logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=log_level
)

logger.add(
    handler,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG"
)



logger.debug(f"Logger initialized in {environment} mode with level {log_level}")

def get_logger():
    return logger