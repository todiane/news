"""Minimal MCP (Model Context Protocol) endpoint so Claude can work on the news.

Add https://<your-site>/mcp/ as a custom connector in Claude, with the same value as
MCP_TOKEN in .env sent as a bearer token (or as ?token=... on the URL if your client
can't send headers). Claude can then read new items, write back summaries/tags/scores,
manage feeds and pull a digest, with no API key stored in this app.
"""
import hmac
import json
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt

from .models import Content, RSSFeed

PROTOCOL_VERSION = '2025-03-26'
CATEGORIES = [c[0] for c in RSSFeed.CATEGORY_CHOICES]


def _authorised(request):
    token = settings.MCP_TOKEN
    if not token:
        return False
    header = request.headers.get('Authorization', '')
    supplied = header[7:] if header.startswith('Bearer ') else request.GET.get('token', '')
    return hmac.compare_digest(supplied.encode(), token.encode())


def _item(c, with_text=True):
    data = {
        'id': c.id, 'title': c.title, 'url': c.url, 'source': c.source.name,
        'category': c.category, 'published': c.published_date.isoformat(),
        'summary': c.ai_summary, 'tags': c.ai_tags, 'relevance': c.relevance,
    }
    if with_text:
        data['text'] = strip_tags(c.description)[:1500]
    return data


def list_content_to_process(limit=20):
    qs = Content.objects.filter(ai_processed_at__isnull=True).select_related('source')
    return [_item(c) for c in qs.order_by('-published_date')[:min(int(limit), 50)]]


def save_content_analysis(items):
    saved = 0
    for it in items:
        try:
            c = Content.objects.get(pk=it['id'])
        except (Content.DoesNotExist, KeyError):
            continue
        c.ai_summary = str(it.get('summary', ''))[:1000]
        tags = it.get('tags', '')
        c.ai_tags = (', '.join(tags) if isinstance(tags, list) else str(tags))[:300]
        rel = it.get('relevance')
        c.relevance = max(1, min(5, int(rel))) if rel is not None else None
        if it.get('category') in CATEGORIES:
            c.category = it['category']
        c.ai_processed_at = timezone.now()
        c.save()
        saved += 1
    return {'saved': saved}


def list_top_items(days=7, min_relevance=4, limit=30):
    since = timezone.now() - timedelta(days=int(days))
    qs = Content.objects.filter(published_date__gte=since, relevance__gte=int(min_relevance)) \
        .select_related('source').order_by('-relevance', '-published_date')
    return [_item(c, with_text=False) for c in qs[:min(int(limit), 100)]]


def list_feeds():
    return [{'id': f.id, 'name': f.name, 'url': f.url, 'category': f.category,
             'feed_type': f.feed_type, 'active': f.active, 'error_count': f.error_count,
             'last_fetched': f.last_fetched.isoformat() if f.last_fetched else None}
            for f in RSSFeed.objects.all()]


def add_feed(name, url, category='general', feed_type='article'):
    if category not in CATEGORIES:
        return {'error': f'category must be one of {CATEGORIES}'}
    feed, created = RSSFeed.objects.get_or_create(
        url=url, defaults={'name': name, 'category': category, 'feed_type': feed_type})
    return {'id': feed.id, 'created': created}


def fetch_feeds_now():
    from .services.feed_fetcher import FeedFetcher
    fetcher = FeedFetcher()
    feeds = RSSFeed.objects.filter(active=True)
    for feed in feeds:
        fetcher.fetch_feed(feed)
    return {'fetched_feeds': feeds.count()}


def _schema(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required)}


TOOLS = {
    'list_content_to_process': (
        'Newest news items that have no summary/tags/score yet. Read them, then call save_content_analysis.',
        _schema({'limit': {'type': 'integer', 'description': 'max 50, default 20'}}),
        list_content_to_process),
    'save_content_analysis': (
        'Save a 1-2 sentence summary, topic tags and a 1-5 relevance score (5 = must read for someone keeping up '
        'with AI, SEO and traffic growth) per item. Optionally re-categorise with `category`: '
        + ', '.join(CATEGORIES) + '.',
        _schema({'items': {'type': 'array', 'items': _schema({
            'id': {'type': 'integer'}, 'summary': {'type': 'string'},
            'tags': {'type': 'array', 'items': {'type': 'string'}},
            'relevance': {'type': 'integer', 'minimum': 1, 'maximum': 5},
            'category': {'type': 'string'}}, ['id', 'summary'])}}, ['items']),
        save_content_analysis),
    'list_top_items': (
        'Highest-relevance recent items, for writing a weekly digest.',
        _schema({'days': {'type': 'integer'}, 'min_relevance': {'type': 'integer'}, 'limit': {'type': 'integer'}}),
        list_top_items),
    'list_feeds': ('All configured feeds and their health.', _schema({}), list_feeds),
    'add_feed': (
        'Add an RSS or YouTube feed.',
        _schema({'name': {'type': 'string'}, 'url': {'type': 'string'},
                 'category': {'type': 'string', 'enum': CATEGORIES},
                 'feed_type': {'type': 'string', 'enum': ['article', 'youtube']}}, ['name', 'url']),
        add_feed),
    'fetch_feeds_now': ('Fetch all active feeds immediately.', _schema({}), fetch_feeds_now),
}


def _rpc(msg):
    method, mid, params = msg.get('method'), msg.get('id'), msg.get('params') or {}
    if mid is None:  # notification, no reply
        return None

    def ok(result):
        return {'jsonrpc': '2.0', 'id': mid, 'result': result}

    def err(code, text):
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': code, 'message': text}}

    if method == 'initialize':
        return ok({'protocolVersion': PROTOCOL_VERSION, 'capabilities': {'tools': {}},
                   'serverInfo': {'name': 'djangify-news', 'version': '1.0'}})
    if method == 'ping':
        return ok({})
    if method == 'tools/list':
        return ok({'tools': [{'name': n, 'description': d, 'inputSchema': s}
                             for n, (d, s, _) in TOOLS.items()]})
    if method == 'tools/call':
        name = params.get('name')
        if name not in TOOLS:
            return err(-32602, f'Unknown tool {name}')
        try:
            result = TOOLS[name][2](**(params.get('arguments') or {}))
            return ok({'content': [{'type': 'text', 'text': json.dumps(result, default=str)}]})
        except Exception as e:  # report tool failures to Claude rather than a 500
            return ok({'isError': True, 'content': [{'type': 'text', 'text': f'{type(e).__name__}: {e}'}]})
    return err(-32601, f'Method not found: {method}')


@csrf_exempt
def mcp_endpoint(request):
    if not _authorised(request):
        return HttpResponse('Unauthorized', status=401)
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        body = json.loads(request.body)
    except ValueError:
        return JsonResponse({'jsonrpc': '2.0', 'id': None,
                             'error': {'code': -32700, 'message': 'Parse error'}}, status=400)
    if isinstance(body, list):
        replies = [r for r in map(_rpc, body) if r]
        return JsonResponse(replies, safe=False) if replies else HttpResponse(status=202)
    reply = _rpc(body)
    return JsonResponse(reply) if reply else HttpResponse(status=202)
