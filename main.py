from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount static and upload folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    result_home = {
        "message": "Welcome to the Artist Portfolio!",
    }
    return templates.TemplateResponse("index.html", {"request": request, "result_home": result_home})

@app.get("/admin", response_class=HTMLResponse)
def read_admin(request: Request):
    result_admin = {
        "message": "Welcome to the Artist Portfolio!",
    }
    return templates.TemplateResponse("admin.html", {"request": request, "result": result_admin})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)