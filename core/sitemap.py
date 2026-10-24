# core/sitemap.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from feeds.models import Content

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'privacy_policy', 'terms_policy']

    def location(self, item):
        return reverse(item)

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        # Get unique categories
        return [cat[0] for cat in Content.objects.values_list('category').distinct()]

    def location(self, item):
        return f'/category/{item.lower()}/'