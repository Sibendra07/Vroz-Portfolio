#artist/artist.py
from fastapi import APIRouter, HTTPException
from artist.model import Sketch
from artist.db import collection
from artist.schemas import all_sketches_dict


# artist/artist.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
import uuid
from artist.model import Sketch
from artist.db import collection
from artist.schemas import all_sketches_dict

router = APIRouter()

# Define upload directory
UPLOAD_DIR = "uploads"
# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "sketches"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "videos"), exist_ok=True)

@router.get("/")
async def get_all_sketches():
      
    try:
        # Fetch all sketches from the database
        data = collection.find()

        # Convert the list of sketches into a dictionary format
        all_sketch = all_sketches_dict(data)

        # Return the list of sketches as a response
        response = {
                "status": 200,
                "message": "All Sketches Fetched Successfully",
                "sketches": all_sketch
            }
        return response
    
    except Exception as e:
        # If an error occurs, return the error message
        return HTTPException(status_code=500, detail=f"Some Error has occurred, Please Try Again Later")

@router.post("/")
async def create_sketch(
    title: str = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    sketch: Optional[UploadFile] = File(None),
    for_sale: bool = Form(False),
    is_sold: bool = Form(False),
    price: Optional[float] = Form(2999.99)
):
   # Insert a new sketch into the database
    try:
        # Handle image upload
        image_url = None
        if image:
            # Create a unique filename
            image_filename = f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
            image_path = os.path.join(UPLOAD_DIR, "images", image_filename)
            
            # Save the file
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            # The URL that will be stored in the database
            image_url = f"/uploads/images/{image_filename}"

        # Handle sketch upload
        sketch_url = None
        if sketch:
            # Create a unique filename
            sketch_filename = f"{uuid.uuid4()}{os.path.splitext(sketch.filename)[1]}"
            sketch_path = os.path.join(UPLOAD_DIR, "sketches", sketch_filename)
            
            # Save the file
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            # The URL that will be stored in the database
            sketch_url = f"/uploads/sketches/{sketch_filename}"
        
        # Handle video upload
        video_url = None
        if video:
            # Create a unique filename
            video_filename = f"{uuid.uuid4()}{os.path.splitext(video.filename)[1]}"
            video_path = os.path.join(UPLOAD_DIR, "videos", video_filename)
            
            # Save the file
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            
            # The URL that will be stored in the database
            video_url = f"/uploads/videos/{video_filename}"

        # Create a sketch object
        sketch_obj = Sketch(
            title=title,
            description=description,
            image_url=image_url,
            video_url=video_url,
            sketch_url=sketch_url,
            for_sale=for_sale,
            is_sold=is_sold,
            price=price
        )

        
        # Insert the sketch into the database
        print(sketch_obj)
        result = collection.insert_one(dict(sketch_obj))
        inserted_id = str(result.inserted_id)
        print("inserted id ")
        print(inserted_id)
            
        response = {
                "status": 200,
                "message": "Sketch created successfully",
                "inserted_id": inserted_id
            }
        
        return response
        
    except Exception as e:
        # If an error occurs, return the error message
        return HTTPException(status_code=500, detail=f"Some Error has occurred, Please Try Again Later")