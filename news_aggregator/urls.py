from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from core.sitemap import StaticViewSitemap, CategorySitemap
from core.views import robots_txt
from django.views.static import serve
from feeds.mcp import mcp_endpoint

admin.site.site_header = "Djangify News Aggregator"
admin.site.site_title = "Djangify News Aggregator Admin Portal"
admin.site.index_title = "Welcome to the Djangify News Aggregator Admin Portal"

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('feeds.urls')),  # maintains existing API endpoints
    path('mcp/', mcp_endpoint, name='mcp'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'), 
    path('static/<path:path>', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
] 