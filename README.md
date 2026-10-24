# Diane Corriette's News Aggregator

A news aggregator built with Django and Django REST Framework. It collects the newsletters, blogs and YouTube channels I read and watch on AI, SEO, content creation, creative coding, Python and Django, so I visit one site instead of sorting through an inbox.

Live site: [news.dianecorriette.com](https://news.dianecorriette.com)

![news site](https://raw.githubusercontent.com/todiane/news/main/news.djangify.png)

## Features

- **Automatic aggregation** from RSS, Atom and YouTube feeds, fetched every 6 hours
- **Categories** with a filter that shows four buttons per row (two rows): Artificial Intelligence, Frontend, Backend, Python, SEO, Content Creation and Creative Coding (DevOps, Traffic & Marketing, News, General and YouTube also exist)
- **Search** across titles
- **"Load More"** pagination
- **Daily email digest** of the items added in the last 24 hours, one email a day
- **Claude connector** (MCP) so Claude can summarise, tag and score items, write a digest, and add feeds
- **Adminita admin theme** (Tailwind CSS, dark mode) for managing feeds and content
- **Retention**: items older than 30 days are removed unless pinned or favorited
- **SEO**: sitemap and robots.txt
- **YouTube handling** with proper thumbnails

## Tech stack

- Django 5.2, Python 3.13, Django REST Framework
- feedparser for RSS and Atom
- SQLite (no database server)
- django-environ for `.env` settings
- [Adminita](https://adminita.todiane.com) for the admin theme
- Tailwind CSS 4, Alpine.js
- Optional Redis cache (`REDIS_URL`), otherwise in-memory caching
- Production: gunicorn under systemd, behind Caddy (HTTPS), on a VPS

## Run it locally

```bash
git clone https://github.com/todiane/news.git
cd news
python -m venv venv
venv\Scripts\activate          # Windows. On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # then edit it (see below). On Mac/Linux: cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Local `.env` values:

```
DJANGO_SECRET_KEY=any-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

The site is at http://127.0.0.1:8000/ and the admin at http://127.0.0.1:8000/admin/.

The database starts empty. Add feeds in the admin (Feeds > RSS feeds), then run:

```bash
python manage.py fetch_feeds
```

The `SITE_ID` setting is 2, and a fresh database creates that Site record on `migrate`. Set its domain in the admin (Sites) if you need the sitemap to show your own domain.

### Static files

The app serves static files from `staticfiles/`, so run `python manage.py collectstatic --noinput` after any CSS or JS change.

CSS is Tailwind. After changing templates or `static/src/input.css`:

```bash
npm install
npm run build
python manage.py collectstatic --noinput
```

`static/css/` and `static/js/` are listed in `.gitignore` but the files in them are tracked. To commit a change there use `git add -f static/css/output.css`.

### Tests

```bash
python manage.py test
```

## Feeds

Feeds are rows in the database, not files in the repo, so a new install starts with none. Add them in the admin, or ask Claude through the connector (`add_feed`). The live site currently follows these, by category:

| Category | Feeds |
|---|---|
| Artificial Intelligence | Simon Willison, Claude Blog, Anthropic News, Anthropic Engineering, Anthropic (YouTube) |
| Frontend | Tailwind CSS Blog |
| Backend | Django Weblog |
| Python | Real Python, Python Insider |
| SEO | Search Engine Journal, Search Engine Roundtable, Ahrefs Blog |
| Content Creation | PetaPixel, No Film School, YouTube Official Blog, Social Media Examiner, Creative Bloq |
| Creative Coding | The Coding Train (YouTube), p5.js Releases, Processing Foundation, CodePen Blog, Hugging Face Blog, fxguide |

Notes: Anthropic publishes no RSS of its own. The Claude Blog, Anthropic News and Anthropic Engineering feeds come from the community project [Olshansk/rss-feeds](https://github.com/Olshansk/rss-feeds), so they can go stale if that project stops updating them. Reddit rejects the fetcher's user agent, so Reddit feeds do not work.

## Daily email digest

```bash
python manage.py send_daily_digest --fetch
```

This fetches all feeds, then sends one email (HTML and plain text) listing the items added in the last 24 hours, grouped by category, with up to 8 per category. Items Claude has scored as more relevant come first. If nothing is new, no email is sent.

Options: `--hours 48` (look back further), `--dry-run` (print instead of send), `--to a@example.com` (override recipients).

Set these in `.env` to turn on real sending. Without `EMAIL_HOST` the email is printed in the terminal, so nothing goes out by accident:

```
DIGEST_RECIPIENTS=you@example.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=an-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=you@gmail.com
SITE_URL=https://news.dianecorriette.com
```

For Gmail the password must be an app password. Then schedule it once a day, for example at 7am (this replaces the separate `fetch_feeds` run for that time slot):

```
0 7 * * * cd /home/newsagg/app && /home/newsagg/venv/bin/python manage.py send_daily_digest --fetch
```

## Claude connector (AI summaries, tags, relevance, digest)

The app has no AI API key. It exposes an MCP endpoint at `/mcp/` that Claude connects to.

1. Put a long random string in `MCP_TOKEN` in `.env` and restart the app.
2. In Claude, add a custom connector with the URL `https://news.dianecorriette.com/mcp/` and send the token as `Authorization: Bearer <token>` (or use `https://news.dianecorriette.com/mcp/?token=<token>` if the client cannot send headers).
3. Ask Claude things like "process the new news items", "write this week's AI and SEO digest", or "add the Search Engine Land feed".

Tools: `list_content_to_process`, `save_content_analysis`, `list_top_items`, `list_feeds`, `add_feed`, `fetch_feeds_now`.

## Models

- **RSSFeed**: name, URL, type (article or YouTube), category, active flag, last fetched, error count
- **Content**: title, description, URL, image, published date, category, pinned flag, plus the fields Claude fills in (summary, tags, relevance 1 to 5)
- **Favorite**: links a user to a content item and protects it from cleanup (ready for user accounts later)

## API

Read-only, no authentication, throttled to 100 requests a day for anonymous users.

- `GET /content/` : paginated list. Parameters: `page`, `page_size` (default 12, max 100), `category` (for example `ai`, `seo`, `content`, `creative`)
- `GET /content/<id>/` : one item
- `GET /api/load-more/?page=2&category=seo` : same data, used by the "Load More" button

```bash
curl "https://news.dianecorriette.com/content/?category=creative&page_size=20"
```

Response shape:

```json
{
  "count": 357,
  "next": "https://news.dianecorriette.com/content/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Article title",
      "description": "Article description...",
      "url": "https://source.com/article",
      "image_url": "https://source.com/image.jpg",
      "source_name": "Tech Blog",
      "published_date": "2026-10-23T14:30:00Z",
      "is_pinned": false,
      "category": "python"
    }
  ]
}
```

Site search is the web page `/search/?q=term`, not an API parameter.

## Project structure

```
manage.py
news_aggregator/            settings, urls, wsgi
core/                       home, search, policy pages, sitemap, robots.txt
feeds/
  models.py                 RSSFeed, Content, Favorite
  views.py, serializers.py  REST API
  mcp.py                    Claude connector endpoint
  services/feed_fetcher.py  fetches and stores feed items
  management/commands/
    fetch_feeds.py
    cleanup_old_content.py
    send_daily_digest.py
  migrations/
templates/
  base.html, index.html
  components/               nav, footer, category filter, news card
  email/                    digest.html, digest.txt
  admin/base_site.html
static/
  src/input.css             Tailwind source
  css/                      output.css (built), main.css (colour variables)
```

## Colours

The main colour is `#6B6FD6`. It and its dark, light and accent shades are CSS variables at the top of `static/css/main.css`. Change them there.

## Deployment

Production runs at https://news.dianecorriette.com on a VPS:

- gunicorn (`newsagg.service`, port 8013) under systemd, with the code in `/home/newsagg/app`
- Caddy provides HTTPS and serves `/static/`
- cron runs `fetch_feeds` every 6 hours and `cleanup_old_content` daily at 03:00

To deploy an update after pushing to GitHub:

```bash
ssh corrison
cd /home/newsagg/app
sudo -u newsagg -H git pull
sudo -u newsagg -H /home/newsagg/venv/bin/pip install -r requirements.txt
sudo -u newsagg -H /home/newsagg/venv/bin/python manage.py migrate
sudo -u newsagg -H /home/newsagg/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart newsagg
```

Production settings live in `/home/newsagg/app/.env` on the server (`DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`, `MCP_TOKEN`). With `DEBUG` off, the app trusts Caddy's forwarded HTTPS header and sends session and CSRF cookies over HTTPS only. Generate migrations locally and commit them; do not run `makemigrations` on the server. The feed list is in the database, so a deploy does not change it.

`passenger_wsgi.py` is left over from an earlier cPanel deployment and is not used now.

## Recent updates

- Set the project up from scratch on a new machine: virtual environment, packages, `.env`, SQLite database and migrations
- Installed the Adminita admin theme and set the admin titles
- Changed the main colour to `#6B6FD6`
- Updated the footer links (GitHub, LinkedIn, Instagram) and replaced DevOps with SEO in the Quick Links and on the home page
- Added the Content Creation and Creative Coding categories, and a four-column category filter (two rows)
- Added starter feeds for SEO, content creation, creative coding (p5.js and AI creation) and Claude and Anthropic news
- Added the daily email digest command
- Hardened production cookies and HTTPS handling when `DEBUG` is off
- Deployed to the VPS at news.dianecorriette.com

## Known issues

- **Load More button**: newly loaded articles show their full content instead of the truncated version seen on the first page load.

## Ideas for later

- User accounts and a personal dashboard
- Favorites for signed-in users
- Content analytics (popular categories and sources)
- Multi-category and date range filters
- A web sign-up for the daily digest, instead of recipients set in `.env`

## License

MIT. (There is no LICENSE file in the repo yet; add one if you want the terms spelled out.)

## Connect

Writing my coding journey at [todiane.dev](https://todiane.dev)

Website: [Djangify](https://djangify.com)
