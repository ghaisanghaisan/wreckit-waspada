export const dynamic = "force-dynamic"

export default function Settings() {
  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure application settings</p>
        </div>
        <div className="space-y-4">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">General Settings</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Application-wide configuration options
            </p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">Data Sources</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Manage RSS feeds and data sources
            </p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">User Preferences</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Personalize your dashboard experience
            </p>
          </div>
        </div>
      </section>
    </main>
  )
}
