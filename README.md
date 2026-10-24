# Djangify News Aggregator

I decided to build a news aggregator using Django and Django Rest Framework to collate all the different newsletters and youtube channels I reguarly read/watch. So now, rather than have a ton of emails in my inbox I can visit the site and keep up with the latest news from my favorite educators on the topics of AI, Django, Python and TailwindCSS.

You can visit the site here: [djangify news](https://news.djangify.com)

This is a modern, responsive news aggregator application built with Django and Python that automatically collects and displays content from various RSS feeds across different technology categories.

![djangify news site](https://raw.githubusercontent.com/djangify/news/main/news.djangify.png)


## 🚀 Features

- **Automatic Content Aggregation** - Pulls from multiple RSS and YouTube feeds
- **Category-Based Organization** - Content organized by tech topics (AI, Frontend, Backend, Python, etc.)
- **Responsive UI** - Mobile-friendly design with Tailwind CSS 4.0
- **Content Management** - Admin interface for feed management and content moderation
- **Search Functionality** - Search across all aggregated content
- **Pagination** - Efficient "Load More" functionality for browsing large content collections
- **YouTube Integration** - Special handling for YouTube feeds with proper thumbnail display
- **Content Retention Policy** - Automatic cleanup of content older than 30 days unless pinned or favorited
- **SEO Optimization** - Fully implemented sitemap for better search engine indexing

## 🛠️ Tech Stack

### Backend
- **Django 5.2** - Core web framework
- **Python 3.10** - Programming language
- **Django REST Framework** - For API endpoints
- **Feedparser** - RSS feed parsing library
- **SQLite** - Standard Django database, no server needed
- **Python-dotenv** - Environment variable management
- **cron** - Run `manage.py fetch_feeds` on a schedule

### Frontend
- **Tailwind CSS 4.0** - Latest version of the utility-first CSS framework
- **Alpine.js** - Lightweight JavaScript framework for interactivity
- **jQuery** - JavaScript library for DOM manipulation
- **Responsive Design** - Mobile-first approach

### Scalability & Performance
- **Redis (optional)** - Set `REDIS_URL` in `.env`, otherwise in-memory caching is used
- **Database Optimization** - Proper indexing for improved query performance
- **Content Retention System** - Automatically cleans up old content to maintain database performance

### AI Assistant
- **Claude AI** - Claude is great to cut down the coding time and to provide help with bugs and errors. While it is still easy for Claude to introduce bugs and errors (so a careful overview of what it provides is essential) helping with errors in production and fixing errors in cpanel plus general debugging help is invaluable. The ability to use prompt engineering successfully is essential to avoid teeth pulling and general frustration!

## 📁 Project Structure

```
news_aggregator/
├── manage.py
├── news_aggregator/        # Project settings and configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── core/                  # Core application functionality
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── sitemap.py         # SEO sitemap implementation
├── feeds/                 # Feed management and content fetching
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   ├── services/
│   │   └── feed_fetcher.py
│   ├── management/
│   │   └── commands/
│   │       ├── fetch_feeds.py
│   │       ├── check_content.py
│   │       └── cleanup_old_content.py   # Content retention management
│   └── templatetags/
│       └── news_tags.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── robots.txt
│   ├── components/
│   │   ├── nav.html
│   │   ├── footer.html
│   │   ├── category_filter.html
│   │   └── news_card.html
│   ├── feeds/
│   │   └── content_list.html
│   └── core/
│       ├── privacy_policy.html
│       └── terms_policy.html
└── static/                # Static assets
    ├── css/
    │   ├── output.css
    │   └── main.css
    ├── img/
    ├── js/
    │   ├── main.js
    │   └── category-filter.js
    └── src/
        └── input.css
```

## 🔄 Models & Database Design

### Key Models

- **RSSFeed**: Stores feed metadata (URL, name, category, type)
  - Supports different feed types (article, YouTube)
  - Tracks fetch status and errors
  - Categories include: AI, Frontend, Backend, Python, DevOps, News, General

- **Content**: Unified model for all content types
  - Stores title, description, URL, image/thumbnail
  - Tracks publishing date and source information
  - Supports pinning of important content

- **Favorite**: Links users to their favorite content (prepared for future user authentication)
  - Allows content to be saved by users
  - Prevents automatic deletion of favorited content

## 🔌 API Documentation

The application provides a RESTful API for content retrieval and integration with other systems.

### API Endpoints

#### Content Retrieval

- `GET /feeds/api/content/`
  - **Description**: Retrieve paginated list of all content items
  - **Parameters**:
    - `page` (optional): Page number for pagination (default: 1)
    - `page_size` (optional): Number of items per page (default: 12, max: 100)
    - `category` (optional): Filter by category
  - **Response**:
    ```json
    {
      "count": 357,
      "next": "http://example.com/feeds/api/content/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "title": "Article Title",
          "description": "Article description text...",
          "url": "https://source.com/article-url",
          "image_url": "https://source.com/image.jpg",
          "source_name": "Tech Blog",
          "published_date": "2025-02-22T14:30:00Z",
          "is_pinned": false,
          "category": "python"
        },
        // Additional items...
      ]
    }
    ```

- `GET /feeds/api/content/<id>/`
  - **Description**: Retrieve a specific content item by ID
  - **Response**: Single content item object

#### Load More Content

- `GET /feeds/api/load-more/`
  - **Description**: Specialized endpoint for the "Load More" functionality
  - **Parameters**:
    - `page` (required): Page number to load
    - `category` (optional): Filter by category
  - **Response**: Same format as the content endpoint

#### Search Functionality

- `GET /feeds/api/content/?search=<query>`
  - **Description**: Search content across titles and descriptions
  - **Parameters**:
    - `search` (required): Search query string
    - `page` (optional): Page number for pagination
  - **Response**: Same format as the content endpoint, filtered by search term

### API Usage Examples

#### Fetch the latest AI news

```bash
curl -X GET "https://news.djangify.com/feeds/api/content/?category=ai"
```

#### Search for Python-related articles

```bash
curl -X GET "https://news.djangify.com/feeds/api/content/?search=python"
```

#### Fetch the third page of content with 20 items per page

```bash
curl -X GET "https://news.djangify.com/feeds/api/content/?page=3&page_size=20"
```

### Authentication

Currently, the API is read-only and does not require authentication for content retrieval. Future versions will implement token-based authentication for user features like favorites.

## ⚙️ Implementation Details

### Feed Fetching
- **FeedFetcher Service**: Handles different feed types and formats
- **Error Handling**: Tracks fetch errors and provides retry mechanisms
- **Scheduled Tasks**: Uses Django crontab for regular feed updates
- **YouTube Integration**: Special handling for YouTube feeds with thumbnail extraction

### Content Display
- **Responsive Grid Layout**: Adapts to different screen sizes
- **Lazy Loading**: "Load More" button for pagination
- **Error Handling**: Graceful error handling for failed content loads
- **Image Handling**: Fallback displays for missing images

### Content Retention
- **Automatic Cleanup**: Removes content older than 30 days
- **Preservation Rules**: Keeps pinned content and items marked as favorites
- **Database Optimization**: Maintains reasonable database size for performance

### Search
- Performs text search across titles and descriptions
- Returns paginated results with the same UI as the main content display

### SEO Optimization
- **Sitemap Generation**: Dynamic sitemap of all content and categories
- **Meta Tags**: Proper meta tags for social sharing and SEO
- **Robots.txt**: Configured for optimal crawling

### Caching
- **Redis Cache Implementation**: For frequently accessed content
- **Cache Invalidation**: Smart cache refreshing on content updates
- **Query Optimization**: Caching of expensive database queries

## 📊 Performance Optimizations

- **Database Indexing**: Optimized queries with proper indexes
- **Pagination**: Limited result sets for better performance
- **Content Retention**: Automatic cleanup of old content to maintain database performance
- **Image Optimization**: Proper thumbnail sizes for improved loading times
- **CSS/JS Minification**: Reduced file sizes for faster loading
- **Fetch Limiting**: Only fetches latest entries from feeds to avoid database bloat

## 🧩 Reusable Components

The project includes several reusable Django/UI components:

- **News Card Component**: Displays individual content items
- **Pagination Component**: Handles content pagination
- **Category Filter**: Allows filtering by content category
- **Responsive Navigation**: Mobile-friendly navigation bar
- **Cookie Consent Banner**: GDPR-compliant cookie consent management

## 🔒 Admin Features

The Django admin interface is customized for content management:

- **Feed Management**: Add/edit/remove RSS feeds
- **Content Moderation**: Edit/delete content when needed
- **Content Pinning**: Pin important articles to the top
- **Error Monitoring**: Track and reset feed fetch errors
- **Content Retention Control**: Configure what content should be preserved

## 🚀 Deployment

The application is deployed using cPanel in a production environment:

- **cPanel Configuration**: Configured for shared hosting environments
- **WSGI Application**: Using passenger_wsgi.py for cPanel compatibility
- **Environment Variables**: Configuration via `.env` files
- **Static File Handling**: Configured for production environments
- **Database Migration**: Easy migration scripts for database updates

## 🐛 Known Issues

- **Load More Button UI Inconsistency**: When clicking the "Load More" button, newly loaded articles show their full content instead of the truncated version seen in the initial page load.

## 🏗️ Future Enhancements

- **User Authentication**: User accounts for personalized experiences
- **User Dashboard**: Personal dashboard for registered users
- **Content Favorites**: Allow users to save and organize favorite articles
- **Newsletter Integration**: Email digests of top content
- **Content Analytics**: Track popular categories and sources
- **WebSocket Updates**: Real-time content updates
- **Advanced Filtering**: Multi-category and date range filtering
- **UI Consistency Fix**: Address the Load More button display inconsistency

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Connect
Writing my coding journey at [todiane.dev](https://todiane.dev)

Website: [Djangify](https://djangify.com)


## Setup / deploy

```bash
git pull
pip install -r requirements.txt
cp .env.example .env        # then edit: secret key, ALLOWED_HOSTS, MCP_TOKEN
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser   # first time only
python manage.py test
```

Cron (replaces django-crontab):

```
0 */6 * * * cd /path/to/news && venv/bin/python manage.py fetch_feeds
0 3 * * *   cd /path/to/news && venv/bin/python manage.py cleanup_old_content
```

## Claude connector (AI summaries, tags, relevance, digest)

The app has no AI API key. Instead it exposes an MCP endpoint at `/mcp/` that Claude connects to.

1. Put a long random string in `MCP_TOKEN` in `.env` and restart the app.
2. In Claude, add a custom connector with the URL `https://news.djangify.com/mcp/` and send the token as `Authorization: Bearer <token>` (or use `https://news.djangify.com/mcp/?token=<token>` if the client can't send headers).
3. Ask Claude things like "process the new news items", "write this week's AI and SEO digest", or "add the Search Engine Land feed".

Tools: `list_content_to_process`, `save_content_analysis`, `list_top_items`, `list_feeds`, `add_feed`, `fetch_feeds_now`.
