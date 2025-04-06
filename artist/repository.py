from core.db import collection

class Repository:
    def __init__(self):
        self.collection = collection

    def __repr__(self):
        return f"Repository(name={self.name}, url={self.url})"
    
    def get_sketches(self, query: dict = None):
        data = collection.find(query)
        return data
    
artist_repository = Repository()