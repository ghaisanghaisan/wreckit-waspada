"use client"

import Link from "next/link"
import Image from "next/image"
import { Menu } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

// TODO: Replace navigation labels and hrefs
const navItems = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "About", href: "#about" },
  { label: "Contact", href: "#contact" },
]

export function LandingNavbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* TODO: Replace logo source, alt text, and brand name */}
        <Link href="#" className="flex items-center gap-2">
          <Image
            src="/logo_waspada.png"
            alt="WASPADA LOGO"
            width={32}
            height={32}
            className="rounded"
          />
          <span className="text-base font-extrabold">WASPADA</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {/* TODO: Replace CTA text and link destination */}
          <Button className="hidden md:inline-flex">Get Started</Button>
          <Button variant="outline" className="hidden md:inline-flex">
            <Link href="/login">Login</Link>
          </Button>

          <Sheet>
            <SheetTrigger className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-foreground shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Open navigation</span>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <div className="flex h-full flex-col gap-6 pt-6">
                <div className="flex items-center gap-2">
                  <Image
                    src="/placeholder-logo.svg"
                    alt="Replace with your brand logo"
                    width={28}
                    height={28}
                    className="rounded"
                  />
                  <span className="text-sm font-semibold">Waspada</span>
                </div>
                <div className="flex flex-col gap-3">
                  {navItems.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
                <Button variant="outline" className="w-full">Login</Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
