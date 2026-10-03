import { NextResponse } from "next/server";
import { getUser } from "@/lib/db";
import { getSiteSettings } from "@/lib/settings";

// Signed-in-only read of the payments pause so an open billing page can
// notice a resume without a reload. Exposes nothing beyond that flag.
export async function GET() {
  if (!(await getUser())) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }
  const { payments_paused } = await getSiteSettings();
  return NextResponse.json({ payments_paused });
}
