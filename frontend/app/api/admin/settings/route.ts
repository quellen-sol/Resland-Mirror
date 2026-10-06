import { NextResponse } from "next/server";
import { hidden, requireAdmin } from "@/lib/admin";
import { auth0 } from "@/lib/auth0";
import { getSiteSettings, primeSiteSettingsCache } from "@/lib/settings";

// The admin dashboard's settings surface. Writes forward to the Python API
// (the canonical writer — it upserts the row and flips its own in-process
// flag), then prime the local cache so this deploy sees it instantly.

export async function GET() {
  if (!(await requireAdmin())) return hidden();
  return NextResponse.json(await getSiteSettings());
}

export async function PUT(request: Request) {
  if (!(await requireAdmin())) return hidden();

  const body = (await request.json().catch(() => ({}))) as {
    maintenance_mode?: boolean;
    payments_paused?: boolean;
  };
  const payload: Record<string, boolean> = {};
  if (typeof body.maintenance_mode === "boolean")
    payload.maintenance_mode = body.maintenance_mode;
  if (typeof body.payments_paused === "boolean")
    payload.payments_paused = body.payments_paused;

  let token: string;
  try {
    token = (await auth0.getAccessToken()).token;
  } catch {
    return NextResponse.json(
      { detail: "Couldn't mint an API token" },
      { status: 401 },
    );
  }
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl}/admin/settings`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    return NextResponse.json(
      { detail: "Can't reach the Resland API" },
      { status: 502 },
    );
  }
  if (!res.ok) {
    return NextResponse.json(
      { detail: await res.text() },
      { status: res.status },
    );
  }
  const settings = (await res.json()) as {
    maintenance_mode: boolean;
    payments_paused: boolean;
    updated_at?: string | null;
  };
  primeSiteSettingsCache({
    maintenance_mode: settings.maintenance_mode,
    payments_paused: settings.payments_paused,
    updated_at: settings.updated_at ?? null,
  });
  return NextResponse.json(settings);
}
