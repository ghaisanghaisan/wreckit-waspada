"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SiteHeader } from "@/components/site-header";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";

export const dynamic = "force-dynamic";

type Report = {
  id: string;
  title: string;
  status: string;
  generated_report: string | null;
  requested_at: string;
  urlCount: number;
};

type ReportSummary = {
  totalReports: number;
  draftReports: number;
  finalReports: number;
  pendingArticles: number;
};

function getStatusColor(status: string) {
  switch (status) {
    case "FINAL":
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400";
    case "DRAFT":
      return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400";
    case "PENDING":
      return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400";
  }
}

function truncateText(text: string | null, maxLength: number = 200): string {
  if (!text) return "No summary available";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [summary, setSummary] = useState<ReportSummary>({
    totalReports: 0,
    draftReports: 0,
    finalReports: 0,
    pendingArticles: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [reportsRes, summaryRes] = await Promise.all([
          fetch("/api/reports"),
          fetch("/api/reports/summary"),
        ]);

        if (reportsRes.ok) {
          const data = await reportsRes.json();
          setReports(data);
        }

        if (summaryRes.ok) {
          const data = await summaryRes.json();
          setSummary(data);
        }
      } catch (error) {
        console.error("Failed to fetch reports:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <main>
      <SiteHeader title="Reports" />
      <div className="flex flex-1 flex-col">
        <div className="@container/main flex flex-1 flex-col gap-2">
          <div className="grid grid-cols-1 gap-4 py-4 md:gap-6 md:py-6 lg:grid-cols-3">
            {/* Left Column - Main Content */}
            <div className="col-span-1 flex flex-col gap-4 px-4 lg:col-span-2 lg:px-6">
              {/* Header */}
              <div className="space-y-2">
                <h1 className="text-3xl font-bold">Reports</h1>
                <p className="text-muted-foreground">
                  Generate and manage your reports
                </p>
              </div>

              {/* Generate Report Button */}
              <Button
                variant="destructive"
                size="lg"
                className="w-full gap-2 py-6 text-base"
              >
                <Plus className="size-5" />
                Generate New Report
              </Button>

              {/* Reports List */}
              <div className="flex flex-col gap-3">
                {loading ? (
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="h-48 rounded-lg border bg-card animate-pulse"
                      />
                    ))}
                  </div>
                ) : reports.length > 0 ? (
                  reports.map((report) => (
                    <Card key={report.id} className="flex flex-col">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <CardTitle>{report.title}</CardTitle>
                            <CardDescription className="mt-1">
                              {report.requested_at} • {report.urlCount} URL
                              {report.urlCount !== 1 ? "s" : ""}
                            </CardDescription>
                          </div>
                          <Badge className={getStatusColor(report.status)}>
                            {report.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {truncateText(report.generated_report)}
                        </p>
                      </CardContent>
                      <CardFooter className="text-xs text-muted-foreground">
                        <button className="text-primary hover:underline">
                          View Full Report →
                        </button>
                      </CardFooter>
                    </Card>
                  ))
                ) : (
                  <Card className="flex items-center justify-center py-12">
                    <CardContent className="text-center">
                      <p className="text-muted-foreground">
                        No reports yet. Create your first report to get started.
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Right Column - Stats Sidebar */}
            <div className="col-span-1 flex flex-col gap-4 px-4 lg:px-6">
              <div className="grid grid-cols-1 gap-3 @xl:grid-cols-2 lg:grid-cols-1">
                {/* Total Reports Card */}
                <Card className="bg-linear-to-t from-primary/5 to-card shadow-xs dark:bg-card">
                  <CardHeader>
                    <CardDescription>Total Reports</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums">
                      {summary.totalReports}
                    </CardTitle>
                  </CardHeader>
                </Card>

                {/* Draft Reports Card */}
                <Card className="bg-linear-to-t from-amber-500/5 to-card shadow-xs dark:bg-card">
                  <CardHeader>
                    <CardDescription>Draft Reports</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums">
                      {summary.draftReports}
                    </CardTitle>
                  </CardHeader>
                </Card>

                {/* Final Reports Card */}
                <Card className="bg-linear-to-t from-emerald-500/5 to-card shadow-xs dark:bg-card">
                  <CardHeader>
                    <CardDescription>Final Reports</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums">
                      {summary.finalReports}
                    </CardTitle>
                  </CardHeader>
                </Card>

                {/* Pending Articles Card */}
                <Card className="bg-linear-to-t from-blue-500/5 to-card shadow-xs dark:bg-card">
                  <CardHeader>
                    <CardDescription>Pending Articles</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums">
                      {summary.pendingArticles}
                    </CardTitle>
                  </CardHeader>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
