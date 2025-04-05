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

    #Authentication settings (Auth Module)

    # JWT settings
    SECRET_KEY = os.getenv("SECRET_KEY", "cLBXZ1yXcS3qBUqZF9PXn436Kg7kVFpN2xjgi2lz1Qg") # Ensure this is a long, random string in .env
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    # Admin credentials from environment
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$Hk8mMV4Fj2Lp0p6ofHnycOuBhw30TlQg7v/FZzOtKwI66i7dQN3vS")

# Create an instance of the config
config = Config()