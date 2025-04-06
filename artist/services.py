from fastapi import HTTPException

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
      data = artist_repository.get_sketches(query=query)
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