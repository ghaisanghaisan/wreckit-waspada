import { SentimentDonut } from "@/components/statistics/sentiment-donut"
import { SentimentSeries } from "@/components/statistics/sentiment-series"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { sql } from "@/lib/db"

export const dynamic = "force-dynamic"

export type SentimentTotals = {
  positive: number
  negative: number
}

export type SentimentDataPoint = {
  time: string
  positive: number
  negative: number
}

async function fetchTotals(): Promise<SentimentTotals> {
  const rows = await sql<SentimentTotals[]>`
    select
      count(*) filter (where sentiment = 'POSITIF')::int as positive,
      count(*) filter (where sentiment = 'NEGATIF')::int as negative
    from news_articles
  `

  return rows[0] ?? { positive: 0, negative: 0 }
}

async function fetchTimeSeries(): Promise<SentimentDataPoint[]> {
  const rows = await sql<SentimentDataPoint[]>`
    with buckets as (
      select generate_series(
        date_trunc('day', now()) - interval '6 days',
        date_trunc('day', now()),
        interval '1 day'
      ) as bucket
    )
    select
      to_char(b.bucket, 'Mon DD') as time,
      count(a.*) filter (where a.sentiment = 'POSITIF')::int as positive,
      count(a.*) filter (where a.sentiment = 'NEGATIF')::int as negative
    from buckets b
    left join news_articles a
      on date_trunc('day', coalesce(a.published_at, a.scraped_at)) = b.bucket
    group by b.bucket
    order by b.bucket
  `

  return rows
}

export default async function MonitorStatistics() {
  const [totals, series] = await Promise.all([
    fetchTotals(),
    fetchTimeSeries(),
  ])

  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-3xl font-bold">Monitor Statistics</h1>
          <p className="text-muted-foreground">Detailed statistics and analytics</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Totals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs text-muted-foreground">Positive</p>
                  <p className="text-2xl font-semibold">{totals.positive}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Negative</p>
                  <p className="text-2xl font-semibold">{totals.negative}</p>
                </div>
              </div>
              <div className="mt-6">
                <SentimentDonut totals={totals} />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <SentimentSeries data={series} />
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
