import os
from fastapi import FastAPI, Request, Form, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import shutil
import uuid
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import RedirectResponse

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# Ensure required folders exist
def ensure_folders():
    required_folders = [
        "static",
        "uploads",
        "uploads/sketch_sales",
        "uploads/image_sketches"
    ]
    for folder in required_folders:
        os.makedirs(folder, exist_ok=True)

# Call the function to ensure folders are created
ensure_folders()

# Mount static and upload folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Get sensitive data from environment variables
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_password")
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./default.db")

# Database setup
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: DeclarativeMeta = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database models
class SketchSale(Base):
    __tablename__ = "sketch_sales"
    id = Column(Integer, primary_key=True, index=True)
    sketch_image = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    is_sold = Column(Boolean, default=False)

class ImageSketch(Base):
    __tablename__ = "image_sketches"
    id = Column(Integer, primary_key=True, index=True)
    photo_image = Column(String, nullable=False)
    sketch_image = Column(String, nullable=False)
    description = Column(String, nullable=False)

# Create the database tables
Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    sketch_sales = db.query(SketchSale).all()
    image_sketches = db.query(ImageSketch).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "sketch_sales": sketch_sales, "image_sketches": image_sketches},
    )
@app.get("/products", response_class=HTMLResponse)
def products(request: Request, db: Session = Depends(get_db)):
    # Query all sketch sales
    sketch_sales = db.query(SketchSale).all()
    
    # Convert to a list of dictionaries
    products = [
        {
            "id": sale.id,
            "imageUrl": sale.sketch_image,
            "name": sale.description,
            "price": f"${sale.price:.2f}",
        }
        for sale in sketch_sales
    ]
    
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products},
    )

@app.get("/my-work", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    image_sketches = db.query(ImageSketch).all()
    return templates.TemplateResponse(
        "my_work.html",
        {"request": request,"image_sketches": image_sketches},
    )


@app.get("/admin", response_class=HTMLResponse)
def read_admin(request: Request, db: Session = Depends(get_db)):
    # Check if the user is logged in
    if request.cookies.get("is_admin") != "true":
        return RedirectResponse(url="/admin_login")
    
    sketch_sales = db.query(SketchSale).all()
    image_sketches = db.query(ImageSketch).all()
    return templates.TemplateResponse(
        "admin_combined.html",
        {"request": request, "sketch_sales": sketch_sales, "image_sketches": image_sketches},
    )

@app.post("/admin", response_class=HTMLResponse)
def verify_admin(request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    # Set a cookie to track login state
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="is_admin", value="true", httponly=True)
    return response

@app.post("/logout", response_class=HTMLResponse)
def logout():
    # Clear the admin cookie
    response = RedirectResponse(url="/admin_login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="is_admin")
    return response

@app.get("/admin_login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# Routes for SketchSale
@app.post("/admin/sketch_sales", response_class=HTMLResponse)
def create_sketch_sale(
    request: Request,
    sketch_image: UploadFile = File(...),
    price: float = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    sketch_image_filename = f"{uuid.uuid4()}_{sketch_image.filename}"
    sketch_image_path = f"uploads/sketch_sales/{sketch_image_filename}"
    with open(sketch_image_path, "wb") as buffer:
        shutil.copyfileobj(sketch_image.file, buffer)

    new_sketch_sale = SketchSale(
        sketch_image=f"/uploads/sketch_sales/{sketch_image_filename}",
        price=price,
        description=description,
        is_sold=False
    )
    db.add(new_sketch_sale)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/sketch_sales/{sketch_sale_id}")
def delete_sketch_sale(
    sketch_sale_id: int,
    method: str = Form(...),
    db: Session = Depends(get_db)
):
    if method != "delete":
        raise HTTPException(status_code=405, detail="Method Not Allowed")
    
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    db.delete(sketch_sale)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/sketch_sales/{sketch_sale_id}/edit", response_class=HTMLResponse)
def edit_sketch_sale_form(sketch_sale_id: int, request: Request, db: Session = Depends(get_db)):
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    return templates.TemplateResponse(
        "edit_sketch_sale.html",
        {"request": request, "sketch_sale": sketch_sale},
    )

@app.post("/admin/sketch_sales/{sketch_sale_id}/edit", response_class=HTMLResponse)
def update_sketch_sale(
    sketch_sale_id: int,
    price: float = Form(...),
    description: str = Form(...),
    is_sold: bool = Form(False),
    db: Session = Depends(get_db)
):
    sketch_sale = db.query(SketchSale).filter(SketchSale.id == sketch_sale_id).first()
    if not sketch_sale:
        raise HTTPException(status_code=404, detail="Sketch Sale not found")
    sketch_sale.price = price
    sketch_sale.description = description
    sketch_sale.is_sold = is_sold
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

# Routes for ImageSketch
@app.post("/admin/image_sketches", response_class=HTMLResponse)
def create_image_sketch(
    request: Request,
    photo_image: UploadFile = File(...),
    sketch_image: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    photo_image_filename = f"{uuid.uuid4()}_{photo_image.filename}"
    sketch_image_filename = f"{uuid.uuid4()}_{sketch_image.filename}"
    photo_image_path = f"uploads/image_sketches/{photo_image_filename}"
    sketch_image_path = f"uploads/image_sketches/{sketch_image_filename}"

    with open(photo_image_path, "wb") as buffer:
        shutil.copyfileobj(photo_image.file, buffer)
    with open(sketch_image_path, "wb") as buffer:
        shutil.copyfileobj(sketch_image.file, buffer)

    new_image_sketch = ImageSketch(
        photo_image=f"/uploads/image_sketches/{photo_image_filename}",
        sketch_image=f"/uploads/image_sketches/{sketch_image_filename}",
        description=description
    )
    db.add(new_image_sketch)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/image_sketches/{image_sketch_id}")
def delete_image_sketch(
    image_sketch_id: int,
    method: str = Form(...),
    db: Session = Depends(get_db)
):
    if method != "delete":
        raise HTTPException(status_code=405, detail="Method Not Allowed")
    
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    db.delete(image_sketch)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/image_sketches/{image_sketch_id}/edit", response_class=HTMLResponse)
def edit_image_sketch_form(image_sketch_id: int, request: Request, db: Session = Depends(get_db)):
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    return templates.TemplateResponse(
        "edit_image_sketch.html",
        {"request": request, "image_sketch": image_sketch},
    )

@app.post("/admin/image_sketches/{image_sketch_id}/edit", response_class=HTMLResponse)
def update_image_sketch(
    image_sketch_id: int,
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    image_sketch = db.query(ImageSketch).filter(ImageSketch.id == image_sketch_id).first()
    if not image_sketch:
        raise HTTPException(status_code=404, detail="Image Sketch not found")
    image_sketch.description = description
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return RedirectResponse(url="/")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)