export const dynamic = "force-dynamic"

export default function Reports() {
  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-3xl font-bold">Reports</h1>
          <p className="text-muted-foreground">Generate and view reports</p>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold">Available Reports</h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <div className="size-2 rounded-full bg-primary" />
              Weekly Summary
            </li>
            <li className="flex items-center gap-2">
              <div className="size-2 rounded-full bg-primary" />
              Sentiment Trends
            </li>
            <li className="flex items-center gap-2">
              <div className="size-2 rounded-full bg-primary" />
              Source Performance
            </li>
          </ul>
        </div>
      </section>
    </main>
  )
}
