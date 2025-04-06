from core.db import collection

class Repository:
    def __init__(self):
        self.collection = collection

    def __repr__(self):
        return f"Repository(name={self.name}, url={self.url})"
    
    def find_all(self, query: dict = None):
        data = collection.find(query)
        return data
    
    def find_one(self, query: dict = None):
        data = collection.find_one(query)
        return data
    
artist_repository = Repository()