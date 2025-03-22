from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount static and upload folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Hardcoded admin password
ADMIN_PASSWORD = "admin123"

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    result_home = {
        "message": "Welcome to the Artist Portfolio!",
    }
    return templates.TemplateResponse("index.html", {"request": request, "result_home": result_home})

@app.get("/admin", response_class=HTMLResponse)
def read_admin(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin", response_class=HTMLResponse)
def verify_admin(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    result_admin = {
        "message": "Welcome to the Artist Portfolio!",
    }
    return templates.TemplateResponse("admin.html", {"request": request, "result": result_admin})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)