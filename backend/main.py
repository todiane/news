import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

app = FastAPI()

# Configure templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_path = BASE_DIR / "static"

# Ensure static directory exists
static_path.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "base.html",
        {"request": request}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
