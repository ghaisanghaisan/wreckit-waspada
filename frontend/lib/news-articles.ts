import { sql } from "@/lib/db"

export type NewsArticleRow = {
  id: string
  title: string
  source: string | null
  published_at: string | null
  sentiment: string | null
}

export async function fetchNewsArticles(limit = 50): Promise<NewsArticleRow[]> {
  const rows = await sql<NewsArticleRow[]>`
    select id, title, source, published_at, sentiment
    from news_articles
    order by published_at desc nulls last
    limit ${limit}
  `

  return rows
}
