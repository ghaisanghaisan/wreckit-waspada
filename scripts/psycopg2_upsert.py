"""
Example synchronous ingestion using psycopg2 with TIMESTAMPTZ (UTC) handling
and an UPSERT that avoids duplicate `url` entries.
"""
import os
import datetime
import psycopg2
from psycopg2.extras import Json, register_default_jsonb

register_default_jsonb()

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv is optional; if not installed, environment variables must be set externally
    pass

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', '')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'waspada')

DB_DSN = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DB_DSN)

def upsert_news_article(conn, article: dict):
    """
    article keys: url, source, title, body, author, published_at (datetime)
    Uses ON CONFLICT (url) DO UPDATE to handle duplicates gracefully.
    """
    sql = """
    INSERT INTO news_articles (url, source, title, body, author, published_at, scraped_at, category, tags, raw_html)
    VALUES (%(url)s, %(source)s, %(title)s, %(body)s, %(author)s, %(published_at)s, %(scraped_at)s, %(category)s, %(tags)s, %(raw_html)s)
    ON CONFLICT (url) DO UPDATE SET
      source = EXCLUDED.source,
      title = EXCLUDED.title,
      body = EXCLUDED.body,
      author = EXCLUDED.author,
      published_at = EXCLUDED.published_at,
      scraped_at = EXCLUDED.scraped_at,
      category = EXCLUDED.category,
      tags = EXCLUDED.tags,
      raw_html = EXCLUDED.raw_html;
    """

    with conn.cursor() as cur:
        cur.execute(sql, {
            'url': article['url'],
            'source': article.get('source'),
            'title': article['title'],
            'body': article['body'],
            'author': article.get('author'),
            'published_at': article.get('published_at'),
            'scraped_at': datetime.datetime.now(datetime.timezone.utc),
            'category': article.get('category'),
            'tags': article.get('tags', []),
            'raw_html': article.get('raw_html')
        })
    conn.commit()

def example_usage():
    article = {
        'url': 'https://example.com/article/1',
        'source': 'example.com',
        'title': 'Example Article',
        'body': 'Full body text',
        'author': 'Reporter',
        'published_at': datetime.datetime(2026, 5, 13, 12, 0, tzinfo=datetime.timezone.utc),
        'category': 'news',
        'tags': ['politics', 'world'],
        'raw_html': '<html>...</html>'
    }

    conn = psycopg2.connect(DB_DSN)
    try:
        upsert_news_article(conn, article)
    finally:
        conn.close()

if __name__ == '__main__':
    example_usage()
