import { NextResponse, type NextRequest } from "next/server";
import { Temporal } from "temporal-polyfill";
import { hidden, requireAdmin } from "@/lib/admin";
import {
  coerceTrafficRange,
  summarizeTraffic,
  trafficRangeStart,
  type PageViewRecord,
} from "@/lib/traffic";
import { db } from "@/prisma/db";

// The Traffic panel in /admin: page_view rows for the last 1, 7 or 30 days,
// summarized here. Fine while traffic is small; move the grouping into SQL
// once a month of rows gets heavy.
export async function GET(request: NextRequest) {
  if (!(await requireAdmin())) return hidden();

  const days = coerceTrafficRange(request.nextUrl.searchParams.get("days"));
  const now = new Date();
  const since = Temporal.Instant.from(trafficRangeStart(days, now).toISOString());
  const rows = await db.orm.public.PageView.where((v) => v.created_at.gte(since))
    .select("visit_id", "path", "prev_path", "source", "source_name", "created_at")
    .orderBy((v) => v.id.asc())
    .all();

  const records: PageViewRecord[] = rows.map((r) => ({
    ...r,
    created_at: new Date(String(r.created_at)),
  }));
  return NextResponse.json({ days, ...summarizeTraffic(records, { days, now }) });
}
