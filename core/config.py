import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # FastAPI settings
    HOST = os.getenv("HOST", "0.0.0.0")  # Default to 0.0.0.0 for accessibility
    PORT = int(os.getenv("PORT", 8000))   # Default port 8000
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")  # Convert to boolean

    # MongoDB settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "db_name")  # Moved here
    MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "collection_name")  # Moved here

# Create an instance of the config
config = Config()