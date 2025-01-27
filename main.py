from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="Development News API",
    description="API for fetching and managing development-focused news articles",
    version="0.1.0"
)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Sample data (will be replaced with database data later)
sample_articles = [
    {
        "title": "Python 4.0 Release Date Announced",
        "content": "The Python Steering Council has announced the official release timeline for Python 4.0. This major update brings significant improvements to the language...",
        "url": "#",
        "source": "Python News",
        "published_date": datetime.now()
    },
    {
        "title": "New Features in FastAPI 1.0",
        "content": "FastAPI 1.0 has been released with groundbreaking new features including improved WebSocket support, enhanced dependency injection...",
        "url": "#",
        "source": "FastAPI Blog",
        "published_date": datetime.now()
    },
    {
        "title": "The Future of Web Development",
        "content": "As we look ahead to 2025, several emerging technologies are set to reshape how we build web applications...",
        "url": "#",
        "source": "Tech Insights",
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
async def articles(request: Request):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)