import Link from "next/link"
// import { Github, Linkedin, Twitter } from "lucide-react"

// TODO: Replace footer column titles and links
const footerColumns = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Pricing", href: "#pricing" },
      { label: "Integrations", href: "#" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "#about" },
      { label: "Careers", href: "#" },
      { label: "Contact", href: "#contact" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "#" },
      { label: "Security", href: "#" },
      { label: "Support", href: "#" },
    ],
  },
]

export function LandingFooter() {
  return (
    <footer className="border-t bg-background">
      <div className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-3">
            {/* TODO: Replace brand name and description */}
            <h3 className="text-lg font-semibold">Waspada</h3>
            <p className="text-sm text-muted-foreground">
              Monitoring public narratives with real-time intelligence and resilient workflows.
            </p>
          </div>

          {footerColumns.map((column) => (
            <div key={column.title} className="space-y-3">
              <p className="text-sm font-semibold text-foreground">{column.title}</p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {/* TODO: Replace footer links */}
                    <Link href={link.href} className="hover:text-foreground">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-start justify-between gap-4 border-t pt-6 text-sm text-muted-foreground sm:flex-row sm:items-center">
          {/* TODO: Replace copyright text */}
          <p>© 2026 Waspada. All rights reserved.</p>
          <div className="flex items-center gap-4">
            {/* TODO: Replace social links */}
            {/* <Link href="#" aria-label="Twitter" className="hover:text-foreground">
              <Twitter className="h-4 w-4" />
            </Link>
            <Link href="#" aria-label="LinkedIn" className="hover:text-foreground">
              <Linkedin className="h-4 w-4" />
            </Link>
            <Link href="#" aria-label="GitHub" className="hover:text-foreground">
              <Github className="h-4 w-4" />
            </Link> */}
          </div>
        </div>
      </div>
    </footer>
  )
}
