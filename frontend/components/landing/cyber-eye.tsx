"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type CyberEyeProps = {
  className?: string
}

export function CyberEye({ className }: CyberEyeProps) {
  const containerRef = React.useRef<HTMLDivElement | null>(null)
  const coreRef = React.useRef<HTMLDivElement | null>(null)
  const rafRef = React.useRef<number | null>(null)

  React.useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!containerRef.current || !coreRef.current) {
        return
      }

      const rect = containerRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2

      // Mouse vector from the center of the eye to the cursor.
      const dx = event.clientX - centerX
      const dy = event.clientY - centerY

      // Constrain the core inside an almond-shaped socket using an ellipse clamp.
      // maxX/maxY define the ellipse radii; we clamp the normalized vector so x^2+y^2 <= 1.
      const maxX = rect.width * 0.14
      const maxY = rect.height * 0.08
      const nx = dx / maxX
      const ny = dy / maxY
      const distance = Math.hypot(nx, ny) || 1
      const clamp = distance > 1 ? 1 / distance : 1

      const offsetX = dx * clamp
      const offsetY = dy * clamp

      // Use rAF to keep motion smooth and avoid layout thrashing.
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }

      rafRef.current = requestAnimationFrame(() => {
        if (!coreRef.current) return
        coreRef.current.style.transform = `translate(${offsetX}px, ${offsetY}px)`
      })
    }

    window.addEventListener("mousemove", handleMouseMove)
    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative isolate aspect-5/3 w-full max-w-90",
        className
      )}
    >
      <style>
        {`
          @keyframes cyber-blink {
            0%, 90%, 100% { transform: scaleY(1); }
            92% { transform: scaleY(0.05); }
            95% { transform: scaleY(1); }
          }

          @keyframes cyber-pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 0.9; }
          }
        `}
      </style>

      {/* Outer glow */}
      <div className="absolute inset-0 rounded-[999px] bg-primary/10 blur-2xl" />

      {/* Eye shell */}
      <div className="relative h-full w-full overflow-hidden rounded-full border border-border/60 bg-card shadow-[0_0_40px_hsl(var(--primary)/0.25)] [clip-path:ellipse(52%_38%_at_50%_50%)]">
        {/* Blink overlay (heavy, defined lid). Uses theme tokens mapped in globals.css */}
        <div className=" pointer-events-none absolute inset-0 origin-center bg-foreground/90 shadow-[0_10px_30px_hsl(var(--foreground)/0.45)] [clip-path:ellipse(52%_38%_at_50%_50%)] animate-[cyber-blink_8s_ease-in-out_infinite]" />

        {/* Sclera gradient */}
        <div className="absolute inset-0 bg-linear-to-b from-background via-muted/40 to-background" />

        {/* Unified core (iris + pupil as one object) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            ref={coreRef}
            className="relative flex size-[44%] items-center justify-center rounded-full bg-primary/30 ring-1 ring-primary/50 shadow-[0_0_24px_hsl(var(--primary)/0.55)] transition-transform duration-150 ease-out"
          >
            <div className="absolute inset-2 rounded-full border border-primary/50" />
            <div className="absolute inset-6 rounded-full border border-accent/60 animate-[cyber-pulse_3s_ease-in-out_infinite]" />
            <div className="absolute inset-[18%] rounded-full bg-foreground/80" />
          </div>
        </div>

        {/* HUD accents */}
        <div className="pointer-events-none absolute inset-6 rounded-[999px] border border-dashed border-primary/30" />
        <div className="pointer-events-none absolute inset-10 rounded-[999px] border border-accent/30" />
      </div>
    </div>
  )
}
