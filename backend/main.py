from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.api.v1.endpoints import auth, articles

app = FastAPI(
    title="Development News API",
    description="API for fetching and managing development-focused news articles",
    version="0.1.0"
)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(articles.router, prefix="/api/v1", tags=["articles"])

# Sample data (will be replaced with database data later)
sample_articles = [
    {
        "title": "Python 4.0 Release Date Announced",
        "content": "The Python Steering Council has announced the official release timeline for Python 4.0...",
        "url": "#",
        "source": "Python News",
        "published_date": datetime.now()
    }
]

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "base.html", 
        {"request": request}
    )

@app.get("/articles")
async def articles_view(request: Request):
    return templates.TemplateResponse(
        "articles.html",
        {
            "request": request,
            "articles": sample_articles
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}