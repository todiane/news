from rest_framework import serializers
from .models import RSSFeed, Content

class RSSFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSSFeed
        fields = ['id', 'name', 'url', 'feed_type', 'active', 'last_fetched']

class ContentSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)
    
    class Meta:
        model = Content
        fields = ['id', 'title', 'description', 'url', 'image_url', 
                 'source_name', 'published_date', 'is_pinned', 'category',
                 'ai_summary', 'ai_tags', 'relevance']