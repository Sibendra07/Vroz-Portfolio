#artist/model.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Sketch(BaseModel):
    title: str
    description: str
    image_url: str | None = None
    video_url: str | None = None
    sketch_url: str | None = None
    for_sale: bool = False
    is_sold: bool = True
    price: float = 2999.99
    is_deleted: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()