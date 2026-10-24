# core/views.py
from django.shortcuts import render
from feeds.models import Content, RSSFeed 
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import RequestContext


def get_all_categories():
    """Get all unique categories from the RSSFeed model with their display names"""
    # Get unique categories directly from CATEGORY_CHOICES
    # But only include ones that are actually in use
    used_categories = set(RSSFeed.objects.values_list('category', flat=True).distinct())
    
    # Return a list of tuples (value, display_name) for each category that's in use,
    # in alphabetical order by display name
    in_use = [(cat_value, cat_display) for cat_value, cat_display in RSSFeed.CATEGORY_CHOICES
              if cat_value in used_categories]
    return sorted(in_use, key=lambda cat: cat[1].lower())

def index(request, category=None):
    # Get all unique categories for navigation
    all_categories = get_all_categories()
    
    # Get content filtered by category if provided
    if category:
        queryset = Content.objects.filter(category__iexact=category).order_by('-published_date')
    else:
        queryset = Content.objects.all().order_by('-published_date')
    
    # Calculate total pages for pagination info
    page_size = 12  # Use the same page size as in ContentPagination
    total_count = queryset.count()
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    # Get first page of content
    content_list = queryset[:page_size]
    
    # Create context with all needed variables
    context = {
        'content_list': content_list,
        'all_categories': all_categories,
        'category': category,
        'category_choices': dict(RSSFeed.CATEGORY_CHOICES),
        'total_pages': total_pages,
        'total_count': total_count
    }
    
    return render(request, 'index.html', context)

def search(request):
    query = request.GET.get('q', '')
    queryset = Content.objects.filter(title__icontains=query).order_by('-published_date')
    all_categories = get_all_categories()
    
    # Calculate total pages for pagination info
    page_size = 12  # Use the same page size as in ContentPagination
    total_count = queryset.count()
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    # Get first page of content
    content_list = queryset[:page_size]
    
    context = {
        'content_list': content_list,
        'query': query,
        'all_categories': all_categories,
        'category_choices': dict(RSSFeed.CATEGORY_CHOICES),
        'total_pages': total_pages,
        'total_count': total_count
    }
    return render(request, 'index.html', context)


def privacy_policy(request):
    # Get all unique categories for navigation
    all_categories = get_all_categories()
    
    context = {
        'all_categories': all_categories,
        'category_choices': dict(RSSFeed.CATEGORY_CHOICES)
    }
    return render(request, 'core/privacy_policy.html', context)


def terms_policy(request):
    # Get all unique categories for navigation
    all_categories = get_all_categories()
    
    context = {
        'all_categories': all_categories,
        'category_choices': dict(RSSFeed.CATEGORY_CHOICES)
    }
    return render(request, 'core/terms_policy.html', context)


def robots_txt(request):
    content = render_to_string('robots.txt', {'request': request})
    return HttpResponse(content, content_type='text/plain')

