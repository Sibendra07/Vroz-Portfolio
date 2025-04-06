from fastapi import HTTPException
from bson.objectid import ObjectId

from core.logger import logger
from core.db import collection
from artist.schemas import all_sketches_dict, individual_sketch_dict
from artist.repository import artist_repository


def get_sketches(only_deleted: bool = False, include_deleted: bool = False):

   try:
      logger.info(f"Fetching all sketches from the database (include_deleted={include_deleted} only_deleted={only_deleted}")
      query = {}
      if only_deleted:
            query["is_deleted"] = True
      elif not include_deleted:
            query["is_deleted"] = {"$ne": True}

      # Fetch all sketches from the database
      data = artist_repository.find_all(query=query)
      if not data:
            logger.warning("No sketches found in the database")
            return "No sketches available in the database"
      logger.info(f"Fetched data : {data}")

      # Convert the list of sketches into a dictionary format
      all_sketch = all_sketches_dict(data)

      logger.info(f"Fetched {len(all_sketch)} sketches successfully")
      return all_sketch
   except Exception as e:
      logger.error(f"Error fetching sketches: {e}")
      raise HTTPException(status_code=500, detail="Failed while fetching sketches")
   

def get_sketch(sketch_id: str, include_deleted: bool = False):
   # Validate the ObjectId format
   try:
      if not ObjectId.is_valid(sketch_id):
         logger.warning(f"Invalid sketch ID format: {sketch_id}")
         raise HTTPException(status_code=400, detail="Invalid sketch ID format")
      
      # Prepare query
      query = {"_id": ObjectId(sketch_id)}
      if not include_deleted:
         query["is_deleted"] = {"$ne": True}
      
      # Fetch the sketch from the database
      sketch = artist_repository.find_one(query=query)
      
      if not sketch:
         logger.warning(f"Sketch with ID {sketch_id} not found or is deleted")
         raise HTTPException(status_code=404, detail="Sketch not found")
      
      # Convert the sketch document to a dictionary
      sketch_data = individual_sketch_dict(sketch)
      if not sketch_data:
         logger.warning(f"Sketch data is empty for ID: {sketch_id}")
         raise HTTPException(status_code=404, detail="Sketch data is empty")
      
      logger.info(f"Successfully fetched sketch with ID: {sketch_id}")
      return sketch_data
   except HTTPException as e:
      logger.error(f"HTTP error: {e.detail}")
      raise HTTPException(status_code=500, detail="Failed while fetching sketch by ID")
   except Exception as e:
      logger.error(f"Error fetching sketch by ID: {e}")
      raise HTTPException(status_code=500, detail="Failed while fetching sketch by ID")