# At the top of main.py, add/update these imports
from fastapi import BackgroundTasks
from app.core.middleware import RateLimitMiddleware
from app.core.background_tasks import background_task_manager
from fastapi import FastAPI, Request, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List
import math

# Import your models and schemas
from app.models.user import User
from app.models.feed import Feed
from app.models.article import Article
from app.core.deps import get_current_user
from app.db.base import get_db
from app.api.v1.endpoints import auth, articles, admin, feed

# Import your routers
from app.api.v1.endpoints import auth, articles, admin
from app.api.v1.endpoints import feed


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

@app.get("/feeds")
async def feeds_view(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Feed management dashboard view."""
    feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
    return templates.TemplateResponse(
        "feeds.html",
        {
            "request": request,
            "feeds": feeds
        }
    )

@app.get("/reader")
async def reader_view(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    content_type: str = Query('all', regex='^(all|videos|articles)$'),
    category: str = Query('all'),
    search: str = Query(''),
    items_per_page: int = 12
):
    """Content reader view with support for articles and videos."""
    # Get user's feeds
    user_feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
    feed_ids = [feed.id for feed in user_feeds]
    
    # Build content query
    query = db.query(Article).filter(Article.feed_id.in_(feed_ids))
    
    # Apply filters
    if content_type == 'videos':
        query = query.filter(Article.api_source == 'youtube')
    elif content_type == 'articles':
        query = query.filter(Article.api_source != 'youtube')
    
    if category != 'all':
        query = query.filter(Article.category == category)
    
    if search:
        search_filter = or_(
            Article.title.ilike(f"%{search}%"),
            Article.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count for pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)
    
    # Apply pagination
    offset = (page - 1) * items_per_page
    query = query.order_by(Article.published_date.desc())
    items = query.offset(offset).limit(items_per_page).all()
    
    # Get unique categories for filter dropdown
    categories = (
        db.query(Article.category)
        .filter(Article.feed_id.in_(feed_ids))
        .distinct()
        .filter(Article.category.isnot(None))
        .all()
    )
    categories = [cat[0] for cat in categories]  # Extract category names
    
    return templates.TemplateResponse(
        "reader.html",
        {
            "request": request,
            "items": items,
            "categories": categories,
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "content_type": content_type,
            "current_category": category,
            "search_query": search
        }
    )

@app.get("/api/v1/reader")
async def reader_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    content_type: str = Query('all', regex='^(all|videos|articles)$'),
    category: str = Query('all'),
    search: str = Query(''),
    items_per_page: int = 12
):
    """API endpoint for fetching reader content with filters."""
    # Get user's feeds
    user_feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
    feed_ids = [feed.id for feed in user_feeds]
    
    # Build content query
    query = db.query(Article).filter(Article.feed_id.in_(feed_ids))
    
    # Apply filters
    if content_type == 'videos':
        query = query.filter(Article.api_source == 'youtube')
    elif content_type == 'articles':
        query = query.filter(Article.api_source != 'youtube')
    
    if category != 'all':
        query = query.filter(Article.category == category)
    
    if search:
        search_filter = or_(
            Article.title.ilike(f"%{search}%"),
            Article.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count for pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)
    
    # Apply pagination
    offset = (page - 1) * items_per_page
    query = query.order_by(Article.published_date.desc())
    items = query.offset(offset).limit(items_per_page).all()
    
    return {
        "items": [item.dict() for item in items],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page
    }
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request}
    )

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        "auth/register.html", 
        {"request": request}
    )

@app.get("/verify-email")
async def verify_email_page(request: Request):
    token = request.query_params.get("token")
    return templates.TemplateResponse(
        "auth/verify-result.html",
        {
            "request": request,
            "token": token
        }
    )

@app.get("/auth/verify-email-sent")
async def verify_email_sent_page(request: Request):
    return templates.TemplateResponse(
        "auth/verify-email-sent.html", 
        {"request": request}
    )

@app.get("/profile")
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "auth/profile.html",
        {
            "request": request,
            "user": current_user,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error")
        }
    )

@app.get("/forgot-password")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "auth/password-reset.html", 
        {"request": request}
    )

@app.get("/reset-password")
async def reset_password_page(request: Request):
    token = request.query_params.get("token")
    return templates.TemplateResponse(
        "auth/password-reset.html",
        {
            "request": request,
            "token": token
        }
    )

