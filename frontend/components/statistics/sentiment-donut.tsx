"use client"

import { Pie, PieChart, Label } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import type { SentimentTotals } from "@/app/dashboard/monitor/statistics/page"

type SentimentDonutProps = {
  totals: SentimentTotals
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

export function SentimentDonut({ totals }: SentimentDonutProps) {
  const data = [
    { name: "Positive", value: totals.positive, fill: "blue" },
    { name: "Negative", value: totals.negative, fill: "red" },
  ]

  const total = totals.positive + totals.negative

  return (
    <ChartContainer className="h-[240px]" config={chartConfig}>
      <PieChart>
        <ChartTooltip
          content={<ChartTooltipContent nameKey="name" indicator="dot" />}
        />
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={70}
          outerRadius={90}
          strokeWidth={4}
        >
          <Label
            position="center"
            content={({ viewBox }) => {
              if (!viewBox || !("cx" in viewBox) || !total) {
                return null
              }

              return (
                <text
                  x={viewBox.cx}
                  y={viewBox.cy}
                  textAnchor="middle"
                  dominantBaseline="middle"
                >
                  <tspan className="fill-foreground text-lg font-semibold">
                    {total}
                  </tspan>
                  <tspan
                    x={viewBox.cx}
                    y={(viewBox.cy ?? 0) + 18}
                    className="fill-muted-foreground text-xs"
                  >
                    total
                  </tspan>
                </text>
              )
            }}
          />
        </Pie>
      </PieChart>
    </ChartContainer>
  )
}
