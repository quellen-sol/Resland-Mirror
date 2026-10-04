// Public pages stay up for everyone while maintenance mode is on — the
// landing page shows a banner instead. Everything else (the signed-in app
// and its API routes) gets the maintenance page unless you're a site admin.
// The page-view beacon stays open so those public pages still count visits.
const PUBLIC_PATHS = new Set(["/", "/help", "/dsa", "/api/metrics/pageview"]);

// DSA study center topics are prerendered with nothing behind them. Their
// progress comes from /api/dsa/progress, which stays gated, and the pages
// hide progress when that request fails.
const DSA_TOPIC_PATH = /^\/dsa\/[a-z0-9-]+$/;

// The share cards for those pages. The proxy's matcher only skips the root
// one, so the nested ones come through here.
const SHARE_IMAGE_PATH = /^(\/dsa(\/[a-z0-9-]+)?)?\/opengraph-image$/;

export function isOpenDuringMaintenance(pathname: string): boolean {
  // Auth routes stay open so admins can sign in.
  return (
    PUBLIC_PATHS.has(pathname) ||
    DSA_TOPIC_PATH.test(pathname) ||
    SHARE_IMAGE_PATH.test(pathname) ||
    pathname.startsWith("/auth/")
  );
}
