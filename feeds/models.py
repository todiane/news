from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

class RSSFeed(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    FEED_TYPES = [
        ('article', 'Article Feed'),
        ('youtube', 'YouTube Feed'),
    ]
    feed_type = models.CharField(max_length=10, choices=FEED_TYPES, default='article')
    
    # Add category choices
    CATEGORY_CHOICES = [
        ('ai', 'Artificial Intelligence'),
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('python', 'Python'),
        ('devops', 'DevOps'),
        ('seo', 'SEO'),
        ('traffic', 'Traffic & Marketing'),
        ('content', 'Content Creation'),
        ('creative', 'Creative Coding'),
        ('news', 'News'),
        ('general', 'General'),
        ('youtube', 'YouTube'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    
    active = models.BooleanField(default=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def fetch_feed_content(self):
      """Manually trigger feed fetch"""
      from .services.feed_fetcher import FeedFetcher
      fetcher = FeedFetcher()
      fetcher.fetch_feed(self)

    def reset_error_count(self):
      """Reset the error counter"""
      self.error_count = 0
      self.save()

class Content(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    url = models.URLField(max_length=2000)
    image_url = models.URLField(max_length=2000, null=True, blank=True)
    published_date = models.DateTimeField()
    is_pinned = models.BooleanField(default=False)
    category = models.CharField(max_length=50, null=True, blank=True, default="General")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.ForeignKey('RSSFeed', on_delete=models.CASCADE, db_index=True)

    # Filled in by Claude through the /mcp/ connector (see feeds/mcp.py)
    ai_summary = models.TextField(blank=True)
    ai_tags = models.CharField(max_length=300, blank=True, help_text='Comma-separated topic tags')
    relevance = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text='1 (skip) to 5 (must read), set by Claude')
    ai_processed_at = models.DateTimeField(null=True, blank=True)

    @property
    def tag_list(self):
        return [t.strip() for t in self.ai_tags.split(',') if t.strip()]

    @property
    def display_summary(self):
        return self.ai_summary or self.description

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-is_pinned', '-published_date']
        indexes = [
            models.Index(fields=['published_date', 'category']),  # Compound index for common queries
        ]

@receiver(post_save, sender=Content)
def clear_content_cache(sender, instance, **kwargs):
    # Clear cache when content is updated
    cache.delete('homepage_news_items')

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content')
        
    def __str__(self):
        return f"{self.user.username} - {self.content.title[:30]}"