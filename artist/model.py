#artist/model.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Sketch(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    sketch_url: str
    for_sale: bool = False
    is_sold: bool = True
    price: Optional[float] = 2999.99
    is_deleted: bool = False
    created_at: int = int(datetime.timestamp(datetime.now()))  
    updated_at: int = int(datetime.timestamp(datetime.now()))