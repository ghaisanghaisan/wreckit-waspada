import Link from "next/link"
import Image from "next/image"
import { CyberEye } from "./cyber-eye"

import { Button } from "@/components/ui/button"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-background py-20 sm:py-24">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 sm:px-6 lg:flex-row lg:items-center">
        <div className="flex-1 space-y-6">
          {/* TODO: Replace headline and subheadline copy */}
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">
            "The Eye that Never Sleeps"
          </p>
          <h1 className="animate-in fade-in-0 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
Autonomous Cyber Intelligence and AI-Driven Threat Detection
          </h1>
          <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
Monitor the digital landscape with autonomous AI capable of identifying sentiment shifts, coordinated messaging, and information operations at scale.
          </p>

          <div className="flex flex-wrap gap-3">
            {/* TODO: Replace CTA labels and destinations */}
            <Button size="lg">
              <Link href="/signup">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline">
              <Link href="#about">Learn More</Link>
            </Button>
          </div>
        </div>

        <div className="flex-1 ">

          <div className="relative flex justify-center items-center h-80 w-full overflow-hidden rounded-2xl shadow-sm sm:h-95">
            {/* <Image
              src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmYxM2luMXlxdXFqeTRsYWJqcWp1cGlmY3A4Y3c4cTJwZTZqMG1tcSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ohs4CacylzFaHjMM8/giphy.gif"
              alt="Product demo GIF - replace this alt with descriptive text" // <-- update alt
              fill
              className="object-cover rounded-xl"
              unoptimized // keeps original GIF; remove if you added domain in next.config.js and want optimization
              priority={false}
            /> */}
            <CyberEye/>
          </div>
        </div>
      </div>
    </section>
  )
}
