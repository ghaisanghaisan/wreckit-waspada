"use client"

import * as React from "react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"

import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group"

export const description = "An interactive sentiment area chart"

const chartData = [
  { date: "2026-04-01", positive: 222, negative: 150 },
  { date: "2026-04-02", positive: 97, negative: 180 },
  { date: "2026-04-03", positive: 167, negative: 120 },
  { date: "2026-04-04", positive: 242, negative: 260 },
  { date: "2026-04-05", positive: 373, negative: 290 },
  { date: "2026-04-06", positive: 301, negative: 340 },
  { date: "2026-04-07", positive: 245, negative: 180 },
  { date: "2026-04-08", positive: 409, negative: 320 },
  { date: "2026-04-09", positive: 59, negative: 110 },
  { date: "2026-04-10", positive: 261, negative: 190 },
  { date: "2026-04-11", positive: 327, negative: 350 },
  { date: "2026-04-12", positive: 292, negative: 210 },
  { date: "2026-04-13", positive: 342, negative: 380 },
  { date: "2026-04-14", positive: 137, negative: 220 },
  { date: "2026-04-15", positive: 120, negative: 170 },
  { date: "2026-04-16", positive: 138, negative: 190 },
  { date: "2026-04-17", positive: 446, negative: 360 },
  { date: "2026-04-18", positive: 364, negative: 410 },
  { date: "2026-04-19", positive: 243, negative: 180 },
  { date: "2026-04-20", positive: 89, negative: 150 },
  { date: "2026-04-21", positive: 137, negative: 200 },
  { date: "2026-04-22", positive: 224, negative: 170 },
  { date: "2026-04-23", positive: 138, negative: 230 },
  { date: "2026-04-24", positive: 387, negative: 290 },
  { date: "2026-04-25", positive: 215, negative: 250 },
  { date: "2026-04-26", positive: 75, negative: 130 },
  { date: "2026-04-27", positive: 383, negative: 420 },
  { date: "2026-04-28", positive: 122, negative: 180 },
  { date: "2026-04-29", positive: 315, negative: 240 },
  { date: "2026-04-30", positive: 454, negative: 380 },
  { date: "2026-05-01", positive: 165, negative: 220 },
  { date: "2026-05-02", positive: 293, negative: 310 },
  { date: "2026-05-03", positive: 247, negative: 190 },
  { date: "2026-05-04", positive: 385, negative: 420 },
  { date: "2026-05-05", positive: 481, negative: 390 },
  { date: "2026-05-06", positive: 498, negative: 520 },
  { date: "2026-05-07", positive: 388, negative: 300 },
  { date: "2026-05-08", positive: 149, negative: 210 },
  { date: "2026-05-09", positive: 227, negative: 180 },
  { date: "2026-05-10", positive: 293, negative: 330 },
  { date: "2026-05-11", positive: 335, negative: 270 },
  { date: "2026-05-12", positive: 197, negative: 240 },
  { date: "2026-05-13", positive: 197, negative: 160 },
  { date: "2026-05-14", positive: 448, negative: 490 },
  { date: "2026-05-15", positive: 473, negative: 380 },
  { date: "2026-05-16", positive: 338, negative: 400 },
  { date: "2026-05-17", positive: 499, negative: 420 },
  { date: "2026-05-18", positive: 315, negative: 350 },
  { date: "2026-05-19", positive: 235, negative: 180 },
  { date: "2026-05-20", positive: 177, negative: 230 },
  { date: "2026-05-21", positive: 82, negative: 140 },
  { date: "2026-05-22", positive: 81, negative: 120 },
  { date: "2026-05-23", positive: 252, negative: 290 },
  { date: "2026-05-24", positive: 294, negative: 220 },
  { date: "2026-05-25", positive: 201, negative: 250 },
  { date: "2026-05-26", positive: 213, negative: 170 },
  { date: "2026-05-27", positive: 420, negative: 460 },
  { date: "2026-05-28", positive: 233, negative: 190 },
  { date: "2026-05-29", positive: 78, negative: 130 },
  { date: "2026-05-30", positive: 340, negative: 280 },
  { date: "2026-05-31", positive: 178, negative: 230 },
  { date: "2026-06-01", positive: 178, negative: 200 },
  { date: "2026-06-02", positive: 470, negative: 410 },
  { date: "2026-06-03", positive: 103, negative: 160 },
  { date: "2026-06-04", positive: 439, negative: 380 },
  { date: "2026-06-05", positive: 88, negative: 140 },
  { date: "2026-06-06", positive: 294, negative: 250 },
  { date: "2026-06-07", positive: 323, negative: 370 },
  { date: "2026-06-08", positive: 385, negative: 320 },
  { date: "2026-06-09", positive: 438, negative: 480 },
  { date: "2026-06-10", positive: 155, negative: 200 },
  { date: "2026-06-11", positive: 92, negative: 150 },
  { date: "2026-06-12", positive: 492, negative: 420 },
  { date: "2026-06-13", positive: 81, negative: 130 },
  { date: "2026-06-14", positive: 426, negative: 380 },
  { date: "2026-06-15", positive: 307, negative: 350 },
  { date: "2026-06-16", positive: 371, negative: 310 },
  { date: "2026-06-17", positive: 475, negative: 520 },
  { date: "2026-06-18", positive: 107, negative: 170 },
  { date: "2026-06-19", positive: 341, negative: 290 },
  { date: "2026-06-20", positive: 408, negative: 450 },
  { date: "2026-06-21", positive: 169, negative: 210 },
  { date: "2026-06-22", positive: 317, negative: 270 },
  { date: "2026-06-23", positive: 480, negative: 530 },
  { date: "2026-06-24", positive: 132, negative: 180 },
  { date: "2026-06-25", positive: 141, negative: 190 },
  { date: "2026-06-26", positive: 434, negative: 380 },
  { date: "2026-06-27", positive: 448, negative: 490 },
  { date: "2026-06-28", positive: 149, negative: 200 },
  { date: "2026-06-29", positive: 103, negative: 160 },
  { date: "2026-06-30", positive: 446, negative: 400 },
]

const chartConfig = {
  positive: {
    label: "Positive Sentiment",
    color: "hsl(var(--chart-1))",
  },
  negative: {
    label: "Negative Sentiment",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig


export function ChartAreaInteractive() {
  const isMobile = useIsMobile()
  const [timeRange, setTimeRange] = React.useState("90d")

  React.useEffect(() => {
    if (isMobile) {
      setTimeRange("7d")
    }
  }, [isMobile])

  const filteredData = chartData.filter((item) => {
    const date = new Date(item.date)
    const referenceDate = new Date("2026-06-30")
    let daysToSubtract = 90
    if (timeRange === "30d") {
      daysToSubtract = 30
    } else if (timeRange === "7d") {
      daysToSubtract = 7
    }
    const startDate = new Date(referenceDate)
    startDate.setDate(startDate.getDate() - daysToSubtract)
    return date >= startDate
  })



  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Sentiment Volume</CardTitle>
        <CardDescription>
          <span className="hidden @[540px]/card:block">
            Total sentiment for the last 3 months
          </span>
          <span className="@[540px]/card:hidden">Last 3 months</span>
        </CardDescription>
        <CardAction>
          <ToggleGroup
            multiple={false}
            value={timeRange ? [timeRange] : []}
            onValueChange={(value) => {
              setTimeRange(value[0] ?? "90d")
            }}
            variant="outline"
            className="hidden *:data-[slot=toggle-group-item]:px-4! @[767px]/card:flex"
          >
            <ToggleGroupItem value="90d">Last 3 months</ToggleGroupItem>
            <ToggleGroupItem value="30d">Last 30 days</ToggleGroupItem>
            <ToggleGroupItem value="7d">Last 7 days</ToggleGroupItem>
          </ToggleGroup>
          <Select
            value={timeRange}
            onValueChange={(value) => {
              if (value !== null) {
                setTimeRange(value)
              }
            }}
          >
            <SelectTrigger
              className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate @[767px]/card:hidden"
              size="sm"
              aria-label="Select a value"
            >
              <SelectValue placeholder="Last 3 months" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="90d" className="rounded-lg">
                Last 3 months
              </SelectItem>
              <SelectItem value="30d" className="rounded-lg">
                Last 30 days
              </SelectItem>
              <SelectItem value="7d" className="rounded-lg">
                Last 7 days
              </SelectItem>
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={filteredData}>
            <defs>
              <linearGradient id="fillPositive" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-positive)"
                  stopOpacity={1.0}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-positive)"
                  stopOpacity={0.1}
                />
              </linearGradient>
              <linearGradient id="fillNegative" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-negative)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-negative)"
                  stopOpacity={0.1}
                />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) => {
                const date = new Date(value)
                return date.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })
              }}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => {
                    return new Date(value).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  }}
                  indicator="dot"
                />
              }
            />
            <Area
              dataKey="negative"
              type="natural"
              fill="url(#fillNegative)"
              stroke="var(--color-negative)"
              stackId="a"
            />
            <Area
              dataKey="positive"
              type="natural"
              fill="url(#fillPositive)"
              stroke="var(--color-positive)"
              stackId="a"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
