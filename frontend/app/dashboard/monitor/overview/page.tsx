export const dynamic = "force-dynamic"

export default function MonitorOverview() {
  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-3xl font-bold">Monitor Overview</h1>
          <p className="text-muted-foreground">System overview and key metrics</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">Total Articles</h3>
            <p className="text-2xl font-bold">0</p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">Positive Sentiment</h3>
            <p className="text-2xl font-bold">0</p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">Neutral Sentiment</h3>
            <p className="text-2xl font-bold">0</p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">Negative Sentiment</h3>
            <p className="text-2xl font-bold">0</p>
          </div>
        </div>
      </section>
    </main>
  )
}
