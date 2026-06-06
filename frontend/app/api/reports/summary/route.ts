import { auth } from "@/lib/auth";
import { getReportsSummary } from "@/lib/reports";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const summary = await getReportsSummary(session.user.id);

    return NextResponse.json(summary);
  } catch (error) {
    console.error("Failed to fetch reports summary:", error);
    return NextResponse.json(
      { error: "Failed to fetch reports summary" },
      { status: 500 },
    );
  }
}
