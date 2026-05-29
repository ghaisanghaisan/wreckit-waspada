import Link from "next/link"

import { Button } from "@/components/ui/button"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-background py-20 sm:py-24">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 sm:px-6 lg:flex-row lg:items-center">
        <div className="flex-1 space-y-6">
          {/* TODO: Replace headline and subheadline copy */}
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">
            Waspada Platform
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Real-time intelligence for high-stakes public sentiment.
          </h1>
          <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
            Streamline monitoring, classify sentiment instantly, and keep your teams informed with a
            workflow built for crisis-response clarity.
          </p>

          <div className="flex flex-wrap gap-3">
            {/* TODO: Replace CTA labels and destinations */}
            <Button size="lg">
              <Link href="#pricing">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline">
              <Link href="#about">Learn More</Link>
            </Button>
          </div>
        </div>

        <div className="flex-1">
          {/* TODO: Replace with Image or product screenshot */}
          <div className="relative h-[320px] w-full overflow-hidden rounded-2xl border bg-gradient-to-br from-primary/10 via-background to-background shadow-sm sm:h-[380px]">
            <div className="absolute inset-6 rounded-xl border bg-background/60 shadow-sm" />
            <div className="absolute left-10 top-10 h-16 w-40 rounded-full bg-primary/10" />
            <div className="absolute bottom-10 right-10 h-20 w-20 rounded-2xl bg-primary/15" />
          </div>
        </div>
      </div>
    </section>
  )
}
