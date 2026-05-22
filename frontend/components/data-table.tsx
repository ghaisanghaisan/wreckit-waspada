import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { NewsArticleRow } from "@/lib/news-articles"

type DataTableProps = {
  data: NewsArticleRow[]
}

function formatDate(value: string | Date | null | undefined) {
  if (!value) return "-"
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return "-"
  return d.toLocaleString()
}

export function DataTable({ data }: DataTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Published</TableHead>
          <TableHead>Sentiment</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.id}>
            <TableCell className="max-w-130 truncate" title={row.title}>
              {row.title}
            </TableCell>
            <TableCell>{row.source ?? "-"}</TableCell>
            <TableCell title={String(row.published_at)}>
              {formatDate(row.published_at as any)}
            </TableCell>
            <TableCell>{row.sentiment ?? "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
