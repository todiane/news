from feedgen.feed import FeedGenerator
from datetime import datetime
from typing import List
from app.schemas.article import Article
from app.core.config import settings

class RSSFeedGenerator:
    def __init__(self):
        self.fg = FeedGenerator()
        self.fg.title('C.A.D News Feed')
        self.fg.description('API for fetching and managing the latest Coding, AI, & Software Developer News, created by Djangify')
        self.fg.link(href=settings.SERVER_HOST)
        self.fg.language('en')

    def add_articles(self, articles: List[Article]):
        for article in articles:
            fe = self.fg.add_entry()
            fe.title(article.title)
            fe.description(article.content)
            fe.link(href=article.url)
            fe.pubDate(article.published_date)
            if article.author:
                fe.author({'name': article.author})

    def get_rss(self) -> str:
        return self.fg.rss_str(pretty=True)

    def get_atom(self) -> str:
        return self.fg.atom_str(pretty=True)
    