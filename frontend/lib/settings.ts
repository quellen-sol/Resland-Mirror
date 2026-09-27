import { db } from "../prisma/db";

// DB-backed kill switches toggled from /admin (site_settings row id=1).
// Cached in-process with a short TTL so the proxy and server components
// don't hit Postgres per request; writes via the /api/admin/settings route
// prime this cache so the toggling deploy sees the change immediately.
export interface SiteSettings {
  maintenance_mode: boolean;
  payments_paused: boolean;
}

const ROW_ID = 1;
const TTL_MS = 15_000;
const OFF: SiteSettings = { maintenance_mode: false, payments_paused: false };

let cache: { value: SiteSettings; expiresAt: number } | null = null;

// The retired env var only seeds the very first row — once the row exists,
// the dashboard owns the flag.
function envMaintenanceSeed(): boolean {
  const v = (process.env.MAINTENANCE_MODE ?? "").trim().toLowerCase();
  return v === "1" || v === "true" || v === "on" || v === "yes";
}

async function fetchSiteSettings(): Promise<SiteSettings> {
  const existing = await db.orm.public.SiteSettings.where((s) =>
    s.id.eq(ROW_ID),
  ).first();
  if (existing) {
    return {
      maintenance_mode: existing.maintenance_mode,
      payments_paused: existing.payments_paused,
    };
  }
  try {
    await db.orm.public.SiteSettings.create({
      id: ROW_ID,
      maintenance_mode: envMaintenanceSeed(),
    });
  } catch {
    // Lost a create race — the row exists now.
  }
  const row = await db.orm.public.SiteSettings.where((s) =>
    s.id.eq(ROW_ID),
  ).first();
  return row
    ? {
        maintenance_mode: row.maintenance_mode,
        payments_paused: row.payments_paused,
      }
    : OFF;
}

export async function getSiteSettings(): Promise<SiteSettings> {
  if (cache && cache.expiresAt > Date.now()) return cache.value;
  try {
    const value = await fetchSiteSettings();
    cache = { value, expiresAt: Date.now() + TTL_MS };
    return value;
  } catch (e) {
    // Fail open on the last-known (or all-off) values — a DB blip must not
    // throw the site into maintenance on its own.
    console.error("site_settings read failed", e);
    return cache?.value ?? OFF;
  }
}

export function primeSiteSettingsCache(value: SiteSettings) {
  cache = { value, expiresAt: Date.now() + TTL_MS };
}
