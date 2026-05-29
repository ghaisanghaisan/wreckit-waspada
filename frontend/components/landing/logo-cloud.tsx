export function LogoCloudSection() {
  // TODO: Replace logo placeholders with real client/partner names or logos
  const logos = [
    "Client Alpha",
    "Client Beta",
    "Client Gamma",
    "Client Delta",
    "Client Epsilon",
    "Client Zeta",
  ]

  return (
    <section className="border-y bg-muted/30 py-12">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        {/* TODO: Replace with your trust/partner statement */}
        <p className="text-center text-sm font-medium text-muted-foreground">
          Trusted by teams monitoring critical public sentiment.
        </p>
        <div className="mt-8 grid grid-cols-2 gap-4 text-center text-sm font-semibold text-muted-foreground sm:grid-cols-3 lg:grid-cols-6">
          {logos.map((logo) => (
            <div
              key={logo}
              className="flex h-12 items-center justify-center rounded-md border border-dashed"
            >
              {/* TODO: Replace with SVG or Image logo */}
              {logo}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
