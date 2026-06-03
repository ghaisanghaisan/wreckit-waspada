import { redirect } from "next/navigation"

import { DataTable } from "@/components/data-table"
import { auth } from "@/lib/auth"
import { fetchNewsArticles } from "@/lib/news-articles"

export const dynamic = "force-dynamic"

export default async function MonitorTable() {
  const session = await auth()
  if (!session?.user?.id) {
    redirect("/login")
  }

  const data = await fetchNewsArticles(session.user.id)

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
