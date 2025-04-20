import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")  # e.g., 'smtp.gmail.com'
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) # e.g., 587 for TLS
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"  # Convert to boolean
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER") # Your email address
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") # Your email password or app password

# Redis Configuration (for Celery)
# Default to localhost if not set in .env
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Application Configuration
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501") # Base URL where the Streamlit app is accessible
COMPLETION_SERVER_URL = os.getenv("COMPLETION_SERVER_URL", "http://localhost:5000") # URL for the Flask completion server
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default-insecure-secret-key-please-change") # Secret key for signing tokens