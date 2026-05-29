import { BarChart3, Bolt, ShieldCheck } from "lucide-react"

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

// TODO: Replace feature titles, descriptions, and icons
const features = [
  {
    title: "Live sentiment signals",
    description:
      "Track breaking news sentiment at scale with adaptive model tuning and rapid updates.",
    icon: BarChart3,
  },
  {
    title: "Operational resilience",
    description:
      "Keep data flowing with resilient ingestion and automatic fallback pipelines.",
    icon: ShieldCheck,
  },
  {
    title: "Actionable alerts",
    description:
      "Deliver instant notifications to the right teams with configurable thresholds.",
    icon: Bolt,
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 sm:py-24">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl space-y-3">
          {/* TODO: Replace section heading and description */}
          <h2 className="text-3xl font-semibold text-foreground sm:text-4xl">
            Everything you need to stay ahead.
          </h2>
          <p className="text-base text-muted-foreground">
            Modular tools designed for security, reliability, and lightning-fast decision making.
          </p>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Card key={feature.title} className="bg-background/80">
                <CardHeader className="space-y-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </div>
    </section>
  )
}
