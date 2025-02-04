# backend/app/api/v1/api.py

from fastapi import APIRouter
from app.api.v1.endpoints import feed_history, auth, articles, feed, admin, subscriptions

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(feed_history.router, prefix="/feed-history", tags=["feed-history"])
