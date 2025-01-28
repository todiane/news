from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, articles
from app.api.v1.endpoints import auth, articles, admin
from app.api.v1.endpoints import feed
from app.core.middleware import RateLimitMiddleware
from app.core.background_tasks import background_task_manager

app = FastAPI(
    title="Development News API",
    description="API for fetching and managing development-focused news articles",
    version="0.1.0"
)

# Add middleware
app.add_middleware(RateLimitMiddleware)

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
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(feed.router, prefix="/api/v1/feed", tags=["feed"])

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
            "articles": []
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts."""
    background_tasks = BackgroundTasks()
    await background_task_manager.start_feed_refresh_task(background_tasks)