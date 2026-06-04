-- Initialization script: creates extensions, schema, and indexes
-- Ensure postgres database name matches the POSTGRES_DB in compose

-- Set database timezone to UTC for timestamptz behavior
ALTER DATABASE waspada SET timezone = 'UTC';

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- agencies table
CREATE TABLE IF NOT EXISTS agencies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- news_articles table
CREATE TABLE IF NOT EXISTS news_articles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  source VARCHAR(100),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  author VARCHAR(255),
  published_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ DEFAULT now(),
  category VARCHAR(100),
  sentiment varchar(10),
  processed_sentiment JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags TEXT[] DEFAULT ARRAY[]::text[],
  raw_html TEXT
);

-- agency_configs table
CREATE TABLE IF NOT EXISTS agency_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  keywords TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
  sentiment_contexts TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_agency_configs_org ON agency_configs (organization_id);

-- report_requests table
CREATE TABLE IF NOT EXISTS report_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  urls JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'PENDING',
  generated_report TEXT,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_report_requests_status ON report_requests (status);
CREATE INDEX IF NOT EXISTS idx_report_requests_requested_at ON report_requests (requested_at);

-- social_posts table
CREATE TABLE IF NOT EXISTS social_posts (
  id VARCHAR(255) PRIMARY KEY,
  platform VARCHAR(50),
  author_id VARCHAR(255),
  author_handle VARCHAR(255),
  content TEXT NOT NULL,
  posted_at TIMESTAMPTZ,
  engagement JSONB NOT NULL DEFAULT '{}'::jsonb,
  media_urls TEXT[] DEFAULT ARRAY[]::text[],
  referenced_url VARCHAR(255),
  parent_post_id VARCHAR(255)
);

-- B-Tree indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_articles_org_url ON news_articles (organization_id, url);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles (source);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles (published_at);
CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_posts (platform);
CREATE INDEX IF NOT EXISTS idx_social_posts_posted_at ON social_posts (posted_at);
CREATE INDEX IF NOT EXISTS idx_social_posts_author_handle ON social_posts (author_handle);

-- GIN indexes for arrays and JSONB
CREATE INDEX IF NOT EXISTS idx_news_articles_tags_gin ON news_articles USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_social_posts_engagement_gin ON social_posts USING GIN (engagement);

-- Optional: trigram index for fast LIKE searches on title/content
CREATE INDEX IF NOT EXISTS idx_news_articles_title_trgm ON news_articles USING gin (title gin_trgm_ops);

-- Example privileges (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres;
