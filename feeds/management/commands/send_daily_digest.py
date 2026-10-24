# feeds/management/commands/send_daily_digest.py
import html
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from feeds.models import Content, RSSFeed

PER_CATEGORY = 8


def clean_text(value):
    """Plain text for an email: no tags, no HTML entities, no 'Read More' leftovers."""
    text = html.unescape(strip_tags(value or ''))
    text = re.sub(r'\[\s*(read more|…|\.\.\.)\s*\]', '', text, flags=re.I)
    return ' '.join(text.split())


class Command(BaseCommand):
    help = 'Email one digest of the news items added in the last day'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='How far back to look (default 24)')
        parser.add_argument('--fetch', action='store_true', help='Fetch all feeds first')
        parser.add_argument('--dry-run', action='store_true', help='Print the digest instead of sending it')
        parser.add_argument('--to', nargs='+', help='Recipients (default: DIGEST_RECIPIENTS in .env)')

    def handle(self, *args, **options):
        if options['fetch']:
            call_command('fetch_feeds', stdout=self.stdout)

        recipients = options['to'] or settings.DIGEST_RECIPIENTS
        if not recipients and not options['dry_run']:
            raise CommandError('No recipients. Set DIGEST_RECIPIENTS in .env or pass --to.')

        since = timezone.now() - timedelta(hours=options['hours'])
        items = Content.objects.filter(created_at__gte=since).select_related('source')
        # Claude-scored items first, then newest
        items = sorted(items, key=lambda c: (-(c.relevance or 0), -c.published_date.timestamp()))
        if not items:
            self.stdout.write('No new items, no email sent.')
            return

        names = dict(RSSFeed.CATEGORY_CHOICES)
        groups = {}
        for c in items:
            group = groups.setdefault(c.source.category, [])
            if len(group) < PER_CATEGORY:
                text = clean_text(c.display_summary)
                group.append({
                    'title': clean_text(c.title),
                    'url': c.url,
                    'source': c.source.name,
                    'summary': text if len(text) <= 220 else text[:217].rstrip() + '...',
                })
        sections = [
            {'name': names.get(cat, cat.title()), 'items': entries}
            for cat, entries in groups.items()
        ]
        count = sum(len(s['items']) for s in sections)

        context = {'sections': sections, 'count': count, 'site_url': settings.SITE_URL,
                   'date': timezone.localdate()}
        text_body = render_to_string('email/digest.txt', context)
        html_body = render_to_string('email/digest.html', context)
        subject = f"Djangify News: {count} new item{'s' if count != 1 else ''} for {context['date']:%d %b %Y}"

        if options['dry_run']:
            # Windows terminals can't print every emoji, so replace what they can't show
            encoding = getattr(self.stdout._out, 'encoding', None) or 'utf-8'
            preview = (subject + '\n\n' + text_body).encode(encoding, 'replace').decode(encoding)
            self.stdout.write(preview)
            return

        message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipients)
        message.attach_alternative(html_body, 'text/html')
        message.send()
        self.stdout.write(self.style.SUCCESS(f'Sent digest of {count} items to {", ".join(recipients)}'))
