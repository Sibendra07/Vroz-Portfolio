
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from core.config import config

# Create a new client and connect to the server
client = MongoClient(config.MONGODB_URI, server_api=ServerApi('1'))

db = client[config.MONGODB_DB_NAME]
collection = db[config.MONGODB_COLLECTION_NAME]