# backend/main.py
from fastapi import FastAPI, BackgroundTasks, Request, Depends, Query, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import math
import logging
from datetime import datetime

# Import middleware and background tasks
from app.core.middleware import RateLimitMiddleware
from app.core.background_tasks import background_task_manager, BackgroundTasks

from app.core.notification_manager import NotificationManager
from app.core.feed_fetcher import FeedFetcher

# Import error handling and versioning
from app.core.error_handler import error_handler, ErrorDetail
from app.core.versioning import version_config, APIVersion, VersionedResponse

# Import models and schemas
from app.models.user import User
from app.models.feed import Feed
from app.models.article import Article
from app.core.deps import get_current_user
from app.db.base import get_db

# Import routers
from app.api.v1.endpoints import auth, articles, admin, feed
from app.api.v1.api import api_router


# Create instances
notification_manager = NotificationManager()
feed_fetcher = FeedFetcher()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Development News API",
    description="API for fetching and managing development-focused news articles",
    version=APIVersion.V1,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input data",
            details={"errors": [{"loc": err["loc"], "msg": err["msg"]} for err in exc.errors()]}
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details=getattr(exc, "details", None)
        ).dict(),
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorDetail(
            code="DATABASE_ERROR",
            message="A database error occurred",
            details={"error": str(exc)} if app.debug else None
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error": str(exc)} if app.debug else None
        ).dict()
    )

# Middleware
app.add_middleware(RateLimitMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Version header middleware
@app.middleware("http")
async def add_version_header(request: Request, call_next):
    """Add API version header to all responses."""
    response = await call_next(request)
    response.headers["X-API-Version"] = APIVersion.V1
    return response

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts."""
    try:
        background_tasks = BackgroundTasks()
        await background_task_manager.start(background_tasks)
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")
        raise


# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks when the application shuts down."""
    try:
        await background_task_manager.stop()
        logger.info("Background tasks stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping background tasks: {e}")


# Health Check
@app.get("/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": APIVersion.V1,
        "timestamp": datetime.utcnow().isoformat()
    }

# Frontend views
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

@app.post("/api/v1/feeds/{feed_id}/refresh")
async def refresh_feed(
    feed_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    # Get new articles
    new_articles = await feed_fetcher.fetch_feed(feed.url)
    
    if new_articles:
        # Send notifications in background
        background_tasks.add_task(
            notification_manager.notify_feed_updates,
            current_user,
            feed_id,
            new_articles
        )
    
    return {"status": "success", "new_articles": len(new_articles)}




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


@app.get("/subscriptions")
async def subscriptions_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscription management page."""
    return templates.TemplateResponse(
        "feed/subscriptions.html",
        {
            "request": request,
            "user": current_user
        }
    )

