import { sql } from "@/lib/db"

export type NewsArticleRow = {
  id: string
  title: string
  source: string
  sentiment: string
  scraped_at: string
  confidence: string
}

export async function fetchNewsArticles(agencyId: string, limit = 50): Promise<NewsArticleRow[]> {
  const rows = await sql<
    {
      id: string
      title: string
      source: string
      sentiment: string
      scraped_at: string | null
      confidence_percent: number | null
    }[]
  >`
    with base as (
      select
        id,
        title,
        coalesce(source, 'Unknown') as source,
        coalesce(sentiment, 'UNKNOWN') as sentiment,
        scraped_at,
        coalesce(processed_sentiment, '{}'::jsonb) as processed_sentiment
      from news_articles
      where organization_id = ${agencyId}
      order by scraped_at desc nulls last
      limit ${limit}
    )
    select
      id,
      title,
      source,
      sentiment,
      to_char(scraped_at, 'YYYY-MM-DD HH24:MI') as scraped_at,
      case
        when (
          select count(*)
          from jsonb_each(processed_sentiment)
        ) = 0 then 0
        when sentiment = 'POSITIF' then
          round(
            100 * (
              select count(*)::numeric
              from jsonb_each(processed_sentiment) as kv
              where kv.value->>'label' = 'POSITIF'
            ) / (
              select count(*)::numeric
              from jsonb_each(processed_sentiment)
            )
          )
        when sentiment = 'NEGATIF' then
          round(
            100 * (
              select count(*)::numeric
              from jsonb_each(processed_sentiment) as kv
              where kv.value->>'label' = 'NEGATIF'
            ) / (
              select count(*)::numeric
              from jsonb_each(processed_sentiment)
            )
          )
        else 0
      end as confidence_percent
    from base
  `

  return rows.map((row) => ({
    id: row.id,
    title: row.title,
    source: row.source,
    sentiment: row.sentiment,
    scraped_at: row.scraped_at ?? "-",
    confidence: `${Math.round(row.confidence_percent ?? 0)}%`,
  }))
}
