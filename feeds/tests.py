import json
from datetime import timedelta
from time import gmtime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Content, RSSFeed
from .services.feed_fetcher import FeedFetcher


class SiteTests(TestCase):
    def setUp(self):
        self.feed = RSSFeed.objects.create(name='Test', url='https://example.com/rss', category='ai')
        self.item = Content.objects.create(
            title='Hello', description='<p>Body</p>', url='https://example.com/a',
            source=self.feed, published_date=timezone.now(), category='ai')

    def test_pages_render(self):
        for name in ('home', 'privacy_policy', 'terms_policy'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(reverse('home')), 'Test')  # source name on card
        self.assertEqual(self.client.get('/search/?q=Hello').status_code, 200)
        self.assertEqual(self.client.get('/category/ai/').status_code, 200)

    def test_robots_and_sitemap(self):
        r = self.client.get('/robots.txt')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('/*?*', r.content.decode())
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)

    def test_load_more_api(self):
        data = self.client.get(reverse('load_more_content')).json()
        self.assertEqual(data['count'], 1)

    def test_entry_date_uses_feed_time(self):
        d = FeedFetcher().entry_date({'published_parsed': gmtime(0)})
        self.assertEqual(d.year, 1970)


@override_settings(MCP_TOKEN='secret')
class MCPTests(TestCase):
    def setUp(self):
        feed = RSSFeed.objects.create(name='Test', url='https://example.com/rss')
        self.item = Content.objects.create(
            title='Hello', description='<p>Body</p>', url='https://example.com/a',
            source=feed, published_date=timezone.now())

    def rpc(self, method, params=None, token='secret'):
        return self.client.post(
            '/mcp/', json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}),
            content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')

    def call(self, name, args=None):
        r = self.rpc('tools/call', {'name': name, 'arguments': args or {}}).json()
        return json.loads(r['result']['content'][0]['text'])

    def test_auth(self):
        self.assertEqual(self.rpc('tools/list', token='wrong').status_code, 401)
        self.assertEqual(self.client.post('/mcp/', '{}', content_type='application/json').status_code, 401)

    @override_settings(MCP_TOKEN='')
    def test_disabled_without_token(self):
        self.assertEqual(self.rpc('tools/list', token='').status_code, 401)

    def test_query_token(self):
        r = self.client.post('/mcp/?token=secret', json.dumps(
            {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}), content_type='application/json')
        self.assertEqual(r.status_code, 200)

    def test_tools_list_and_workflow(self):
        names = [t['name'] for t in self.rpc('tools/list').json()['result']['tools']]
        self.assertIn('save_content_analysis', names)
        todo = self.call('list_content_to_process')
        self.assertEqual(todo[0]['text'], 'Body')
        self.call('save_content_analysis', {'items': [
            {'id': self.item.id, 'summary': 'Short.', 'tags': ['ai', 'seo'], 'relevance': 9}]})
        self.item.refresh_from_db()
        self.assertEqual((self.item.ai_tags, self.item.relevance), ('ai, seo', 5))
        self.assertEqual(self.call('list_content_to_process'), [])
        self.assertEqual(len(self.call('list_top_items')), 1)

    def test_add_feed(self):
        self.assertTrue(self.call('add_feed', {'name': 'X', 'url': 'https://x.com/rss', 'category': 'seo'})['created'])
        self.assertIn('error', self.call('add_feed', {'name': 'Y', 'url': 'https://y.com/rss', 'category': 'nope'}))
