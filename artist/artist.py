from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Path
from typing import Optional, List
import os
import shutil
import uuid
from bson.objectid import ObjectId
from artist.model import Sketch
from datetime import datetime
from core.db import collection
from artist.schemas import all_sketches_dict, individual_sketch_dict
from core.logger import logger


router = APIRouter()

# Define upload directory
UPLOAD_DIR = "uploads"
# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "sketches"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)

# Helper function for file uploads
async def save_upload_file(upload_file: UploadFile, directory: str) -> str:
    if not upload_file or not upload_file.filename:
        return None
        
    filename = f"{uuid.uuid4()}{os.path.splitext(upload_file.filename)[1]}"
    file_path = os.path.join(UPLOAD_DIR, directory, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return f"/uploads/{directory}/{filename}"

@router.get("/")
async def get_all_sketches(include_deleted: bool = False, only_deleted: bool = False):
    logger.info(f"Fetching all sketches from the database (include_deleted={include_deleted})")
      
    try:
        # Prepare query to filter sketches based on deletion status
        query = {}
        if only_deleted:
            query["is_deleted"] = True
        elif not include_deleted:
            query["is_deleted"] = {"$ne": True}

        # Fetch all sketches from the database
        data = collection.find(query)

        # Convert the list of sketches into a dictionary format
        all_sketch = all_sketches_dict(data)

        if not all_sketch:
            logger.warning("No sketches found in the database")
            raise HTTPException(status_code=404, detail="No Sketches Found")

        logger.info(f"Fetched {len(all_sketch)} sketches successfully")
        # Return the list of sketches as a response
        response = {
                "status": 200,
                "message": "All Sketches Fetched Successfully",
                "sketches": all_sketch
            }
        return response
    
    except Exception as e:
        logger.error(f"Error fetching sketches: {str(e)}")
        raise HTTPException(status_code=500, detail="Some Error has occurred, Please Try Again Later")

@router.get("/{sketch_id}")
async def get_sketch_by_id(
    sketch_id: str = Path(..., description="The ID of the sketch to retrieve"),
    include_deleted: bool = False
):
    logger.info(f"Fetching sketch with ID: {sketch_id} (include_deleted={include_deleted})")
    
    try:
        # Validate the ObjectId format
        if not ObjectId.is_valid(sketch_id):
            logger.warning(f"Invalid sketch ID format: {sketch_id}")
            raise HTTPException(status_code=400, detail="Invalid sketch ID format")
        
        # Prepare query
        query = {"_id": ObjectId(sketch_id)}
        if not include_deleted:
            query["is_deleted"] = {"$ne": True}
        
        # Fetch the sketch from the database
        sketch = collection.find_one(query)
        
        if not sketch:
            logger.warning(f"Sketch with ID {sketch_id} not found or is deleted")
            raise HTTPException(status_code=404, detail="Sketch not found")
        
        # Convert the sketch document to a dictionary
        sketch_data = individual_sketch_dict(sketch)
        
        logger.info(f"Successfully fetched sketch with ID: {sketch_id}")
        return {
            "status": 200,
            "message": "Sketch Fetched Successfully",
            "sketch": sketch_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sketch: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")

@router.post("/")
async def create_sketch(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(None),
    video: UploadFile = File(None),
    sketch: UploadFile = File(...),  # Making sketch required since sketch_url is required in the model
    for_sale: bool = Form(False),
    is_sold: bool = Form(False),
    price: float = Form(2999.99)
):
    # Log the request
    logger.info("Creating a new sketch")
    logger.debug(f"Received data: title={title}, description={description}, "
                 f"for_sale={for_sale}, is_sold={is_sold}, price={price}")

    try:
        # Handle file uploads
        image_url = await save_upload_file(image, "images")
        video_url = await save_upload_file(video, "videos")
        sketch_url = await save_upload_file(sketch, "sketches")
        
        if not sketch_url:
            raise HTTPException(status_code=400, detail="Sketch file is required")

        # Create sketch object
        sketch_obj = Sketch(
            title=title,
            description=description,
            image_url=image_url,
            video_url=video_url,
            sketch_url=sketch_url,
            for_sale=for_sale,
            is_sold=is_sold,
            price=price,
            is_deleted=False,
            deleted_at=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Insert into MongoDB
        result = collection.insert_one(dict(sketch_obj))
        if not result.acknowledged:
            logger.error("Failed to insert sketch into the database")
            raise HTTPException(status_code=500, detail="Failed to create sketch")

        inserted_id = str(result.inserted_id)
        logger.info(f"Sketch created with ID: {inserted_id}")

        # Response
        return {
            "status": 201,
            "message": "Sketch created successfully",
            "inserted_id": inserted_id
        }

    except FileNotFoundError as e:
        logger.error(f"File system error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")

@router.put("/{sketch_id}")
async def update_sketch(
    sketch_id: str = Path(..., description="The ID of the sketch to update"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    sketch: Optional[UploadFile] = File(None),
    for_sale: Optional[bool] = Form(None),
    is_sold: Optional[bool] = Form(None),
    price: Optional[float] = Form(None)
):
    logger.info(f"Updating sketch with ID: {sketch_id}")
    
    try:
        # Validate the ObjectId format
        if not ObjectId.is_valid(sketch_id):
            logger.warning(f"Invalid sketch ID format: {sketch_id}")
            raise HTTPException(status_code=400, detail="Invalid sketch ID format")
        
        # Check if the sketch exists
        existing_sketch = collection.find_one({"_id": ObjectId(sketch_id)})
        if not existing_sketch:
            logger.warning(f"Sketch with ID {sketch_id} not found")
            raise HTTPException(status_code=404, detail="Sketch not found")
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()  # Always update the updated_at timestamp
        }
        
        # Update text fields if provided
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if for_sale is not None:
            update_data["for_sale"] = for_sale
        if is_sold is not None:
            update_data["is_sold"] = is_sold
        if price is not None:
            update_data["price"] = price
            
        # Handle file uploads
        image_url = await save_upload_file(image, "images")
        if image_url:
            update_data["image_url"] = image_url
            
        video_url = await save_upload_file(video, "videos")
        if video_url:
            update_data["video_url"] = video_url
            
        sketch_url = await save_upload_file(sketch, "sketches")
        if sketch_url:
            update_data["sketch_url"] = sketch_url
        
        # If no updates provided
        if not update_data:
            logger.warning("No update data provided")
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Update the sketch in the database
        result = collection.update_one(
            {"_id": ObjectId(sketch_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            logger.warning(f"No changes made to sketch with ID: {sketch_id}")
            return {
                "status": 200,
                "message": "No changes made to sketch"
            }
        
        logger.info(f"Successfully updated sketch with ID: {sketch_id}")
        return {
            "status": 200,
            "message": "Sketch updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sketch: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")

@router.delete("/{sketch_id}")
async def soft_delete_sketch(sketch_id: str = Path(..., description="The ID of the sketch to soft delete")):
    logger.info(f"Soft deleting sketch with ID: {sketch_id}")
    
    try:
        # Validate the ObjectId format
        if not ObjectId.is_valid(sketch_id):
            logger.warning(f"Invalid sketch ID format: {sketch_id}")
            raise HTTPException(status_code=400, detail="Invalid sketch ID format")
        
        # Check if sketch exists and is not already deleted
        sketch = collection.find_one({
            "_id": ObjectId(sketch_id),
            "is_deleted": {"$ne": True}
        })
        
        if not sketch:
            logger.warning(f"Sketch with ID {sketch_id} not found or already deleted")
            raise HTTPException(status_code=404, detail="Sketch not found or already deleted")
            
        # Soft delete the sketch
        result = collection.update_one(
            {"_id": ObjectId(sketch_id)},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"Failed to soft delete sketch with ID: {sketch_id}")
            raise HTTPException(status_code=500, detail="Failed to soft delete sketch")
        
        logger.info(f"Successfully soft deleted sketch with ID: {sketch_id}")
        return {
            "status": 200,
            "message": "Sketch soft deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error soft deleting sketch: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")

@router.delete("/{sketch_id}/hard")
async def hard_delete_sketch(sketch_id: str = Path(..., description="The ID of the sketch to permanently delete")):
    logger.info(f"Hard deleting sketch with ID: {sketch_id}")
    
    try:
        # Validate the ObjectId format
        if not ObjectId.is_valid(sketch_id):
            logger.warning(f"Invalid sketch ID format: {sketch_id}")
            raise HTTPException(status_code=400, detail="Invalid sketch ID format")
        
        # Find the sketch first to get file paths for deletion
        sketch = collection.find_one({"_id": ObjectId(sketch_id)})
        if not sketch:
            logger.warning(f"Sketch with ID {sketch_id} not found")
            raise HTTPException(status_code=404, detail="Sketch not found")
            
        # Delete the sketch from the database
        result = collection.delete_one({"_id": ObjectId(sketch_id)})
        
        if result.deleted_count == 0:
            logger.warning(f"Failed to hard delete sketch with ID: {sketch_id}")
            raise HTTPException(status_code=500, detail="Failed to hard delete sketch")
            
        # Optional: Delete associated files
        # This is commented out because you might want to keep files for record purposes
        # If you want to delete files, uncomment this section
        """
        try:
            # Delete image file if exists
            if sketch.get("image_url"):
                file_path = os.path.join(".", sketch["image_url"].lstrip("/"))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            # Delete video file if exists
            if sketch.get("video_url"):
                file_path = os.path.join(".", sketch["video_url"].lstrip("/"))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            # Delete sketch file if exists
            if sketch.get("sketch_url"):
                file_path = os.path.join(".", sketch["sketch_url"].lstrip("/"))
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting files: {str(e)}")
            # Continue even if file deletion fails
        """
        
        logger.info(f"Successfully hard deleted sketch with ID: {sketch_id}")
        return {
            "status": 200,
            "message": "Sketch permanently deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hard deleting sketch: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")

@router.post("/{sketch_id}/restore")
async def restore_sketch(sketch_id: str = Path(..., description="The ID of the sketch to restore")):
    logger.info(f"Restoring soft-deleted sketch with ID: {sketch_id}")
    
    try:
        # Validate the ObjectId format
        if not ObjectId.is_valid(sketch_id):
            logger.warning(f"Invalid sketch ID format: {sketch_id}")
            raise HTTPException(status_code=400, detail="Invalid sketch ID format")
        
        # Check if sketch exists and is deleted
        sketch = collection.find_one({
            "_id": ObjectId(sketch_id),
            "is_deleted": True
        })
        
        if not sketch:
            logger.warning(f"Sketch with ID {sketch_id} not found or not deleted")
            raise HTTPException(status_code=404, detail="Sketch not found or not in deleted state")
            
        # Restore the sketch
        result = collection.update_one(
            {"_id": ObjectId(sketch_id)},
            {
                "$set": {
                    "is_deleted": False,
                    "deleted_at": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"Failed to restore sketch with ID: {sketch_id}")
            raise HTTPException(status_code=500, detail="Failed to restore sketch")
        
        logger.info(f"Successfully restored sketch with ID: {sketch_id}")
        return {
            "status": 200,
            "message": "Sketch restored successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring sketch: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred, please try again later")