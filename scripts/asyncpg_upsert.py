"""
Async example using asyncpg showing JSONB and array operator usage.
"""
import os
import asyncio
import datetime
import asyncpg

# Load environment from .env if present
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

async def upsert_social_post(pool, post: dict):
    sql = """
    INSERT INTO social_posts (id, platform, author_id, author_handle, content, posted_at, engagement, media_urls, referenced_url, parent_post_id)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
    ON CONFLICT (id) DO UPDATE SET
      content = EXCLUDED.content,
      posted_at = EXCLUDED.posted_at,
      engagement = EXCLUDED.engagement,
      media_urls = EXCLUDED.media_urls,
      referenced_url = EXCLUDED.referenced_url,
      parent_post_id = EXCLUDED.parent_post_id;
    """
    async with pool.acquire() as conn:
        await conn.execute(sql,
                           post['id'],
                           post.get('platform'),
                           post.get('author_id'),
                           post.get('author_handle'),
                           post['content'],
                           post.get('posted_at'),
                           post.get('engagement', {}),
                           post.get('media_urls', []),
                           post.get('referenced_url'),
                           post.get('parent_post_id'))

async def example():
    pool = await asyncpg.create_pool(dsn=DB_DSN)
    post = {
        'id': '12345678901234567890',
        'platform': 'twitter',
        'author_id': '1111',
        'author_handle': '@example',
        'content': 'This is a sample tweet',
        'posted_at': datetime.datetime.now(datetime.timezone.utc),
        'engagement': {'likes': 150, 'shares': 10},
        'media_urls': ['https://.../image.jpg']
    }
    await upsert_social_post(pool, post)
    await pool.close()

if __name__ == '__main__':
    asyncio.run(example())
