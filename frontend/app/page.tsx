import { DataTable } from "@/components/data-table"
import { fetchNewsArticles } from "@/lib/news-articles"

export const revalidate = 0

export default async function Home() {
  const data = await fetchNewsArticles()

  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto w-full max-w-6xl space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Waspada Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Latest ingested articles
          </p>
        </div>
        <DataTable data={data} />
      </section>
    </main>
  )
}
