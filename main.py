import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, Request, Form, HTTPException, status, Depends, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import shutil
import uuid
import secrets
from datetime import datetime
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import json
from pathlib import Path
from filetype import guess  # Replacement for imghdr

# Load environment variables from .env file
load_dotenv()

# Get sensitive data from environment variables
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_password")
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./default.db")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Ensure required folders exist
def ensure_folders():
    required_folders = [
        "static", 
        "static/js",
        "static/css",
        "static/images",
        "uploads",
        "uploads/sketch_sales",
        "uploads/image_sketches"
    ]
    for folder in required_folders:
        os.makedirs(folder, exist_ok=True)

# Call the function to ensure folders are created
ensure_folders()

# Initialize FastAPI with middleware
middleware = [
    Middleware(SessionMiddleware, secret_key=SECRET_KEY),
    Middleware(GZipMiddleware, minimum_size=1000)
]

app = FastAPI(middleware=middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and upload folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(json=json)  # Add json filter to Jinja2 templates

# Database setup
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models for validation
class SketchSaleCreate(BaseModel):
    price: float = Field(..., gt=0)
    description: str = Field(..., min_length=3, max_length=500)
    
    @field_validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return float(v)

class SketchSaleUpdate(BaseModel):
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    is_sold: Optional[bool] = False
    
    @field_validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return float(v) if v is not None else None

class ImageSketchCreate(BaseModel):
    description: str = Field(..., min_length=3, max_length=500)

class ImageSketchUpdate(BaseModel):
    description: str = Field(..., min_length=3, max_length=500)

# Database models
class SketchSale(Base):
    __tablename__ = "sketch_sales"
    id = Column(Integer, primary_key=True, index=True)
    sketch_image = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    is_sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "imageUrl": self.sketch_image,
            "name": self.description,
            "price": f"${self.price:.2f}",
            "is_sold": self.is_sold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ImageSketch(Base):
    __tablename__ = "image_sketches"
    id = Column(Integer, primary_key=True, index=True)
    photo_image = Column(String, nullable=False)
    sketch_image = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "photo_image": self.photo_image,
            "sketch_image": self.sketch_image,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions for file validation
def validate_image_file(file: UploadFile) -> bool:
    """Validate image file type and size."""
    # Check file extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in valid_extensions:
        return False
    
    # Read file content for validation
    file.file.seek(0)
    header = file.file.read(2048)
    file.file.seek(0)  # Reset file pointer
    
    # Validate with filetype
    file_type = guess(header)
    if not file_type or file_type.mime.split('/')[0] != 'image':
        return False
        
    return True

def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    """Save an upload file to the specified folder and return the filename."""
    filename = f"{uuid.uuid4()}_{upload_file.filename}"
    filepath = f"{folder}/{filename}"
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return filename

# Authentication helper
def verify_admin(request: Request):
    """Verify if user is admin from session cookie."""
    is_admin = request.session.get("is_admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    sketch_sales = db.query(SketchSale).filter(SketchSale.is_sold == False).all()
    image_sketches = db.query(ImageSketch).all()
    
    # Convert to JSON for easier handling in templates
    sketch_sales_json = json.dumps([sale.to_dict() for sale in sketch_sales])
    image_sketches_json = json.dumps([sketch.to_dict() for sketch in image_sketches])
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "sketch_sales": sketch_sales,
            "image_sketches": image_sketches,
            "sketch_sales_json": sketch_sales_json,
            "image_sketches_json": image_sketches_json
        },
    )

@app.get("/products", response_class=HTMLResponse)
async def products(
    request: Request, 
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Calculate pagination
    offset = (page - 1) * limit
    
    # Query sketch sales with pagination
    total = db.query(SketchSale).count()
    sketch_sales = db.query(SketchSale).offset(offset).limit(limit).all()
    
    # Convert to a list of dictionaries
    products = [sale.to_dict() for sale in sketch_sales]
    
    # Ensure we always have a JSON string, even if empty
    sketch_sales_json = json.dumps(products) if products else '[]'
    
    # Pagination info
    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request, 
            "products": products,
            "sketch_sales_json": sketch_sales_json,
            "pagination": pagination
        },
    )

@app.get("/api/products", response_class=JSONResponse)
async def api_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Calculate pagination
    offset = (page - 1) * limit
    
    # Query sketch sales with pagination
    total = db.query(SketchSale).count()
    sketch_sales = db.query(SketchSale).offset(offset).limit(limit).all()
    
    # Convert to a list of dictionaries
    products = [sale.to_dict() for sale in sketch_sales]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "items": products
    }

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Calculate pagination
    offset = (page - 1) * limit
    
    # Query image sketches with pagination
    total = db.query(ImageSketch).count()
    image_sketches = db.query(ImageSketch).offset(offset).limit(limit).all()
    
    # Convert to JSON for JavaScript
    image_sketches_json = json.dumps([sketch.to_dict() for sketch in image_sketches])
    
    # Pagination info
    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }
    
    return templates.TemplateResponse(
        "my_work.html",
        {
            "request": request,
            "image_sketches": image_sketches,
            "image_sketches_json": image_sketches_json,
            "pagination": pagination
        },
    )

@app.get("/api/portfolio", response_class=JSONResponse)
async def api_portfolio(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Calculate pagination
    offset = (page - 1) * limit
    
    # Query image sketches with pagination
    total = db.query(ImageSketch).count()
    image_sketches = db.query(ImageSketch).offset(offset).limit(limit).all()
    
    # Convert to a list of dictionaries
    items = [sketch.to_dict() for sketch in image_sketches]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "items": items
    }

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request, db: Session = Depends(get_db)):
    # Check if the user is logged in
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/admin_login")
    
    sketch_sales = db.query(SketchSale).all()
    image_sketches = db.query(ImageSketch).all()
    
    # Convert to JSON for easier handling in templates
    sketch_sales_json = json.dumps([sale.to_dict() for sale in sketch_sales])
    image_sketches_json = json.dumps([sketch.to_dict() for sketch in image_sketches])
    
    return templates.TemplateResponse(
        "admin_combined.html",
        {
            "request": request, 
            "sketch_sales": sketch_sales, 
            "image_sketches": image_sketches,
            "sketch_sales_json": sketch_sales_json,
            "image_sketches_json": image_sketches_json
        },
    )

@app.post("/admin_login", response_class=HTMLResponse)
async def verify_admin_login(request: Request, password: str = Form(...)):
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    
    # Set session data
    request.session["is_admin"] = True
    
    # Redirect to admin page
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/logout")
async def logout(request: Request):
    # Clear session data
    request.session.clear()
    
    # Redirect to login page
    return RedirectResponse(url="/admin_login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin_login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# Routes for SketchSale
@app.post("/admin/sketch_sales", response_class=HTMLResponse)
async def create_sketch_sale(
    request: Request,
    sketch_image: UploadFile = File(...),
    price: float = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    # Validate input using Pydantic model
    try:
        sketch_data = SketchSaleCreate(price=price, description=description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    
    # Validate image file
    if not validate_image_file(sketch_image):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Supported formats: JPG, PNG, GIF, WebP"
        )
    
    # Save image file
    sketch_image_filename = save_upload_file(sketch_image, "uploads/sketch_sales")
    
    # Create new sketch sale
    new_sketch_sale = SketchSale(
        sketch_image=f"/uploads/sketch_sales/{sketch_image_filename}",
        price=sketch_data.price,
        description=sketch_data.description,
        is_sold=False
    )
    
    db.add(new_sketch_sale)
    db.commit()
    db.refresh(new_sketch_sale)
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/sketch_sales/{sketch_sale_id}")
async def delete_sketch_sale(
    sketch_sale_id: int,
    request: Request,
    method: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    if method != "delete":
        raise HTTPException(status_code=405, detail="Method Not Allowed")
    
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    
    # Delete the image file if it exists
    if sketch_sale.sketch_image:
        file_path = sketch_sale.sketch_image.lstrip('/')
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.delete(sketch_sale)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/sketch_sales/{sketch_sale_id}/edit", response_class=HTMLResponse)
async def edit_sketch_sale_form(
    sketch_sale_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    
    return templates.TemplateResponse(
        "edit_sketch_sale.html",
        {"request": request, "sketch_sale": sketch_sale},
    )

@app.post("/admin/sketch_sales/{sketch_sale_id}/edit", response_class=HTMLResponse)
async def update_sketch_sale(
    sketch_sale_id: int,
    request: Request,
    price: float = Form(...),
    description: str = Form(...),
    is_sold: bool = Form(False),
    new_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    # Validate input using Pydantic model
    try:
        sketch_data = SketchSaleUpdate(price=price, description=description, is_sold=is_sold)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    
    # Update image if provided
    if new_image and new_image.filename:
        # Validate new image
        if not validate_image_file(new_image):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Supported formats: JPG, PNG, GIF, WebP"
            )
        
        # Delete old image if it exists
        if sketch_sale.sketch_image:
            old_file_path = sketch_sale.sketch_image.lstrip('/')
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Save new image
        sketch_image_filename = save_upload_file(new_image, "uploads/sketch_sales")
        sketch_sale.sketch_image = f"/uploads/sketch_sales/{sketch_image_filename}"
    
    # Update other fields
    sketch_sale.price = sketch_data.price
    sketch_sale.description = sketch_data.description
    sketch_sale.is_sold = sketch_data.is_sold
    sketch_sale.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(sketch_sale)
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

# Routes for ImageSketch
@app.post("/admin/image_sketches", response_class=HTMLResponse)
async def create_image_sketch(
    request: Request,
    photo_image: UploadFile = File(...),
    sketch_image: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    # Validate input using Pydantic model
    try:
        image_data = ImageSketchCreate(description=description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    
    # Validate image files
    if not validate_image_file(photo_image) or not validate_image_file(sketch_image):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Supported formats: JPG, PNG, GIF, WebP"
        )
    
    # Save image files
    photo_image_filename = save_upload_file(photo_image, "uploads/image_sketches")
    sketch_image_filename = save_upload_file(sketch_image, "uploads/image_sketches")
    
    # Create new image sketch
    new_image_sketch = ImageSketch(
        photo_image=f"/uploads/image_sketches/{photo_image_filename}",
        sketch_image=f"/uploads/image_sketches/{sketch_image_filename}",
        description=image_data.description
    )
    
    db.add(new_image_sketch)
    db.commit()
    db.refresh(new_image_sketch)
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/image_sketches/{image_sketch_id}")
async def delete_image_sketch(
    image_sketch_id: int,
    request: Request,
    method: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    if method != "delete":
        raise HTTPException(status_code=405, detail="Method Not Allowed")
    
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    
    # Delete image files if they exist
    for image_path in [image_sketch.photo_image, image_sketch.sketch_image]:
        if image_path:
            file_path = image_path.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)
    
    db.delete(image_sketch)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/image_sketches/{image_sketch_id}/edit", response_class=HTMLResponse)
async def edit_image_sketch_form(
    image_sketch_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    
    return templates.TemplateResponse(
        "edit_image_sketch.html",
        {"request": request, "image_sketch": image_sketch},
    )

@app.post("/admin/image_sketches/{image_sketch_id}/edit", response_class=HTMLResponse)
async def update_image_sketch(
    image_sketch_id: int,
    request: Request,
    description: str = Form(...),
    new_photo: UploadFile = File(None),
    new_sketch: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Verify admin
    verify_admin(request)
    
    # Validate input using Pydantic model
    try:
        image_data = ImageSketchUpdate(description=description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    
    # Update photo image if provided
    if new_photo and new_photo.filename:
        # Validate new image
        if not validate_image_file(new_photo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid photo image file. Supported formats: JPG, PNG, GIF, WebP"
            )
        
        # Delete old image if it exists
        if image_sketch.photo_image:
            old_file_path = image_sketch.photo_image.lstrip('/')
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Save new image
        photo_image_filename = save_upload_file(new_photo, "uploads/image_sketches")
        image_sketch.photo_image = f"/uploads/image_sketches/{photo_image_filename}"
    
    # Update sketch image if provided
    if new_sketch and new_sketch.filename:
        # Validate new image
        if not validate_image_file(new_sketch):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sketch image file. Supported formats: JPG, PNG, GIF, WebP"
            )
        
        # Delete old image if it exists
        if image_sketch.sketch_image:
            old_file_path = image_sketch.sketch_image.lstrip('/')
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Save new image
        sketch_image_filename = save_upload_file(new_sketch, "uploads/image_sketches")
        image_sketch.sketch_image = f"/uploads/image_sketches/{sketch_image_filename}"
    
    # Update description
    image_sketch.description = image_data.description
    image_sketch.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(image_sketch)
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "status_code": exc.status_code, "detail": exc.detail}, 
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "status_code": 422, "detail": str(exc)}, 
        status_code=422
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    
    # Development settings
    uvicorn.run(
        "main:app", 
        host="127.0.0.1",  # Use 0.0.0.0 to make it accessible from outside
        port=8000,
        reload=True,  # Enable auto-reload for development
        workers=1  # Use one worker for development
    )