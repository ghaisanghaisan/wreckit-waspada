"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import type { SentimentDataPoint } from "@/app/dashboard/monitor/statistics/page"

type SentimentSeriesProps = {
  data: SentimentDataPoint[]
}

const chartConfig = {
  positive: {
    label: "Positive",
    color: "hsl(var(--chart-1))",
  },
  negative: {
    label: "Negative",
    color: "hsl(var(--chart-2))",
  },
}

export function SentimentSeries({ data }: SentimentSeriesProps) {
  return (
    <ChartContainer className="h-[260px]" config={chartConfig}>
      <AreaChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="time"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <YAxis tickLine={false} axisLine={false} width={28} />
        <ChartTooltip
          content={<ChartTooltipContent indicator="dot" />}
        />
        <Area
          type="monotone"
          dataKey="positive"
          stroke="var(--color-positive)"
          fill="var(--color-positive)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="negative"
          stroke="var(--color-negative)"
          fill="var(--color-negative)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
      </AreaChart>
    </ChartContainer>
  )
}
