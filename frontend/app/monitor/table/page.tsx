import { DataTable } from "@/components/data-table"
import { fetchNewsArticles } from "@/lib/news-articles"

export const dynamic = "force-dynamic"

export default async function MonitorTable() {
  const data = await fetchNewsArticles()

  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-3xl font-bold">Monitor Table View</h1>
          <p className="text-muted-foreground">Latest ingested articles</p>
        </div>
        <DataTable data={data} />
      </section>
    </main>
  )
}
