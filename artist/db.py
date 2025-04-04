
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://sibendra:Sibdein4562@vroz-portfolio.tmuhx8b.mongodb.net/?retryWrites=true&w=majority&appName=Vroz-portfolio"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.artist_db
collection = db["artist_data"]