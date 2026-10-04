// Public pages stay up for everyone while maintenance mode is on — the
// landing page shows a banner instead. Everything else (the signed-in app
// and its API routes) gets the maintenance page unless you're a site admin.
const PUBLIC_PATHS = new Set(["/", "/help"]);

export function isOpenDuringMaintenance(pathname: string): boolean {
  // Auth routes stay open so admins can sign in.
  return PUBLIC_PATHS.has(pathname) || pathname.startsWith("/auth/");
}
