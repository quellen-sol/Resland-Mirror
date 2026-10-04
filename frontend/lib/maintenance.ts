// Public pages stay up for everyone while maintenance mode is on — the
// landing page shows a banner instead. Everything else (the signed-in app
// and its API routes) gets the maintenance page unless you're a site admin.
const PUBLIC_PATHS = new Set(["/", "/help", "/dsa"]);

// DSA study center topics are prerendered with nothing behind them. Their
// progress comes from /api/dsa/progress, which stays gated, and the pages
// hide progress when that request fails.
const DSA_TOPIC_PATH = /^\/dsa\/[a-z0-9-]+$/;

export function isOpenDuringMaintenance(pathname: string): boolean {
  // Auth routes stay open so admins can sign in.
  return (
    PUBLIC_PATHS.has(pathname) ||
    DSA_TOPIC_PATH.test(pathname) ||
    pathname.startsWith("/auth/")
  );
}
