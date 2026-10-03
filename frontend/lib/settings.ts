import { db } from "../prisma/db";

// DB-backed kill switches toggled from /admin (site_settings row id=1).
// Cached in-process so the proxy and server components don't hit Postgres
// per request; writes via the /api/admin/settings route prime this cache so
// the toggling deploy sees the change immediately.
export interface SiteSettings {
  maintenance_mode: boolean;
  payments_paused: boolean;
  updated_at?: string | null;
}

const ROW_ID = 1;
const TTL_MS = 600_000; // 10 minutes
const OFF: SiteSettings = {
  maintenance_mode: false,
  payments_paused: false,
  updated_at: null,
};

let cache: { value: SiteSettings; expiresAt: number } | null = null;

// The retired env var only supplies the pre-seed fallback — once the row
// exists, the dashboard owns the flag.
function envMaintenanceSeed(): boolean {
  const v = (process.env.MAINTENANCE_MODE ?? "").trim().toLowerCase();
  return v === "1" || v === "true" || v === "on" || v === "yes";
}

async function fetchSiteSettings(): Promise<SiteSettings> {
  const row = await db.orm.public.SiteSettings.where((s) =>
    s.id.eq(ROW_ID),
  ).first();
  if (!row) {
    // The Python API is the only seeder (it creates the row from its own
    // env on first read). Until it exists, mirror the retired env check so
    // an env-paused deploy doesn't briefly open through this side.
    return { ...OFF, maintenance_mode: envMaintenanceSeed() };
  }
  return {
    maintenance_mode: row.maintenance_mode,
    payments_paused: row.payments_paused,
    updated_at:
      row.updated_at == null
        ? null
        : new Date(String(row.updated_at)).toISOString(),
  };
}

export async function getSiteSettings(): Promise<SiteSettings> {
  if (cache && cache.expiresAt > Date.now()) return cache.value;
  try {
    const value = await fetchSiteSettings();
    cache = { value, expiresAt: Date.now() + TTL_MS };
    return value;
  } catch (e) {
    // Fail open on the last-known values — a DB blip must not throw the
    // site into maintenance on its own.
    console.error("site_settings read failed", e);
    return cache?.value ?? OFF;
  }
}

export function primeSiteSettingsCache(value: SiteSettings) {
  cache = { value, expiresAt: Date.now() + TTL_MS };
}
