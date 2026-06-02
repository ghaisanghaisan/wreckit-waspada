import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { fetchDashboardMetrics } from "@/lib/dashboard-metrics"
import { cn } from "@/lib/utils"
import { TrendingUpIcon, TrendingDownIcon } from "lucide-react"

const PERIOD_DAYS = 7

type CardMetric = {
  description: string
  value: number
  changePercent: number
  positiveIsGood: boolean
  valueFormat: "count" | "percent"
}

const numberFormatter = new Intl.NumberFormat("en-US")

function formatValue(value: number, format: "count" | "percent"): string {
  if (format === "percent") {
    return `${Math.round(value)}%`
  }

  return numberFormatter.format(Math.round(value))
}

function formatSignedPercent(value: number): string {
  const rounded = Math.round(value * 10) / 10
  const sign = rounded > 0 ? "+" : ""

  return `${sign}${rounded.toFixed(1)}%`
}

function formatUnsignedPercent(value: number): string {
  const rounded = Math.round(Math.abs(value) * 10) / 10

  return `${rounded.toFixed(1)}%`
}

function getTrendClass(changePercent: number, positiveIsGood: boolean): string {
  if (changePercent === 0) {
    return "text-muted-foreground"
  }

  const isImproving = positiveIsGood ? changePercent > 0 : changePercent < 0

  if (isImproving) {
    return "text-emerald-600 dark:text-emerald-400"
  }

  const isCritical = Math.abs(changePercent) >= 20

  return isCritical
    ? "text-rose-600 dark:text-rose-400"
    : "text-amber-600 dark:text-amber-400"
}

export async function SectionCards() {
  const metrics = await fetchDashboardMetrics(PERIOD_DAYS)
  const cards: CardMetric[] = [
    {
      description: "Total Articles This Week",
      value: metrics.totalArticles.current,
      changePercent: metrics.totalArticles.changePercent,
      positiveIsGood: true,
      valueFormat: "count",
    },
    {
      description: "Positive Sentiment",
      value: metrics.positiveSentiment.current,
      changePercent: metrics.positiveSentiment.changePercent,
      positiveIsGood: true,
      valueFormat: "count",
    },
    {
      description: "Negative Sentiment",
      value: metrics.negativeSentiment.current,
      changePercent: metrics.negativeSentiment.changePercent,
      positiveIsGood: false,
      valueFormat: "count",
    },
    {
      description: "Agency Health",
      value: metrics.healthScore.current,
      changePercent: metrics.healthScore.changePercent,
      positiveIsGood: true,
      valueFormat: "percent",
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-linear-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4 dark:*:data-[slot=card]:bg-card">
      {cards.map((card) => {
        const TrendIcon =
          card.changePercent >= 0 ? TrendingUpIcon : TrendingDownIcon
        const trendClass = getTrendClass(
          card.changePercent,
          card.positiveIsGood
        )
        const trendSummary =
          card.changePercent === 0
            ? "No change"
            : `${card.changePercent > 0 ? "Up" : "Down"} ${formatUnsignedPercent(
                card.changePercent
              )}`

        return (
          <Card key={card.description} className="@container/card">
            <CardHeader>
              <CardDescription>{card.description}</CardDescription>
              <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                {formatValue(card.value, card.valueFormat)}
              </CardTitle>
              <CardAction>
                <Badge
                  variant="outline"
                  className={cn("gap-1 border-current", trendClass)}
                >
                  <TrendIcon className="size-4" />
                  {formatSignedPercent(card.changePercent)}
                </Badge>
              </CardAction>
            </CardHeader>
            <CardFooter className="flex-col items-start gap-1.5 text-sm">
              <div
                className={cn("line-clamp-1 flex gap-2 font-medium", trendClass)}
              >
                {trendSummary}
                <TrendIcon className="size-4" />
              </div>
              <div className="text-muted-foreground">
                Compared with previous {PERIOD_DAYS} days
              </div>
            </CardFooter>
          </Card>
        )
      })}
    </div>
  )
}
