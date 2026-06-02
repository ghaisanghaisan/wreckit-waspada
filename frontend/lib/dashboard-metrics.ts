import { sql } from "@/lib/db"

export type TrendMetric = {
  current: number
  previous: number
  changePercent: number
}

export type DashboardMetrics = {
  totalArticles: TrendMetric
  positiveSentiment: TrendMetric
  negativeSentiment: TrendMetric
  healthScore: TrendMetric
}

type DashboardMetricRow = {
  current_total: number
  previous_total: number
  current_positive: number
  previous_positive: number
  current_negative: number
  previous_negative: number
}

export function calculatePercentChange(current: number, previous: number): number {
  if (previous === 0) {
    return current === 0 ? 0 : 100
  }

  return ((current - previous) / previous) * 100
}

function calculateSharePercent(positive: number, negative: number): number {
  const total = positive + negative

  if (total === 0) {
    return 0
  }

  return (positive / total) * 100
}

export async function fetchDashboardMetrics(
  periodDays = 7
): Promise<DashboardMetrics> {
  const now = Date.now()
  const currentStart = new Date(now - periodDays * 24 * 60 * 60 * 1000)
  const previousStart = new Date(now - periodDays * 2 * 24 * 60 * 60 * 1000)

  const rows = await sql<DashboardMetricRow[]>`
    select
      count(*) filter (
        where coalesce(published_at, scraped_at) >= ${currentStart}
      )::int as current_total,
      count(*) filter (
        where coalesce(published_at, scraped_at) >= ${previousStart}
          and coalesce(published_at, scraped_at) < ${currentStart}
      )::int as previous_total,
      count(*) filter (
        where sentiment = 'POSITIF'
          and coalesce(published_at, scraped_at) >= ${currentStart}
      )::int as current_positive,
      count(*) filter (
        where sentiment = 'POSITIF'
          and coalesce(published_at, scraped_at) >= ${previousStart}
          and coalesce(published_at, scraped_at) < ${currentStart}
      )::int as previous_positive,
      count(*) filter (
        where sentiment = 'NEGATIF'
          and coalesce(published_at, scraped_at) >= ${currentStart}
      )::int as current_negative,
      count(*) filter (
        where sentiment = 'NEGATIF'
          and coalesce(published_at, scraped_at) >= ${previousStart}
          and coalesce(published_at, scraped_at) < ${currentStart}
      )::int as previous_negative
    from news_articles
  `

  const row = rows[0] ?? {
    current_total: 0,
    previous_total: 0,
    current_positive: 0,
    previous_positive: 0,
    current_negative: 0,
    previous_negative: 0,
  }

  const currentHealth = calculateSharePercent(
    row.current_positive,
    row.current_negative
  )
  const previousHealth = calculateSharePercent(
    row.previous_positive,
    row.previous_negative
  )

  return {
    totalArticles: {
      current: row.current_total,
      previous: row.previous_total,
      changePercent: calculatePercentChange(
        row.current_total,
        row.previous_total
      ),
    },
    positiveSentiment: {
      current: row.current_positive,
      previous: row.previous_positive,
      changePercent: calculatePercentChange(
        row.current_positive,
        row.previous_positive
      ),
    },
    negativeSentiment: {
      current: row.current_negative,
      previous: row.previous_negative,
      changePercent: calculatePercentChange(
        row.current_negative,
        row.previous_negative
      ),
    },
    healthScore: {
      current: currentHealth,
      previous: previousHealth,
      changePercent: calculatePercentChange(currentHealth, previousHealth),
    },
  }
}
