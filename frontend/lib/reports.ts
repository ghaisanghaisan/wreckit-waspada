import { sql } from "@/lib/db";

export type ReportRow = {
  id: string;
  title: string;
  status: string;
  generated_report: string | null;
  requested_at: string;
  urlCount: number;
};

export type ReportSummary = {
  totalReports: number;
  draftReports: number;
  finalReports: number;
  pendingArticles: number;
};

export async function fetchReports(
  agencyId: string,
  limit = 50,
): Promise<ReportRow[]> {
  const rows = await sql<
    {
      id: string;
      status: string;
      generated_report: string | null;
      requested_at: string | null;
      url_count: number;
    }[]
  >`
    select
      id,
      status,
      generated_report,
      to_char(requested_at, 'YYYY-MM-DD HH24:MI') as requested_at,
      jsonb_array_length(coalesce(urls, '[]'::jsonb)) as url_count
    from report_requests
    where organization_id = ${agencyId}
    order by requested_at desc nulls last
    limit ${limit}
  `;

  return rows.map((row) => ({
    id: row.id,
    title: `Report ${row.requested_at}`,
    status: row.status,
    generated_report: row.generated_report,
    requested_at: row.requested_at ?? "-",
    urlCount: row.url_count,
  }));
}

export async function getPendingArticlesCount(
  agencyId: string,
): Promise<number> {
  const result = await sql<[{ count: number }]>`
    select count(*) as count
    from news_articles
    where 
      organization_id = ${agencyId}
      and id not in (
        select distinct jsonb_array_elements(urls)::uuid
        from report_requests
        where organization_id = ${agencyId}
        and status = 'FINAL'
      )
  `;

  return result[0]?.count ?? 0;
}

export async function getReportsSummary(
  agencyId: string,
): Promise<ReportSummary> {
  const rows = await sql<
    {
      total: number;
      draft: number;
      final: number;
    }[]
  >`
    select
      count(*) as total,
      count(*) filter (where status = 'DRAFT') as draft,
      count(*) filter (where status = 'FINAL') as final
    from report_requests
    where organization_id = ${agencyId}
  `;

  const reportCounts = rows[0] ?? { total: 0, draft: 0, final: 0 };
  const pendingCount = await getPendingArticlesCount(agencyId);

  return {
    totalReports: reportCounts.total,
    draftReports: reportCounts.draft,
    finalReports: reportCounts.final,
    pendingArticles: pendingCount,
  };
}
