import { NextResponse } from "next/server";

import { auth0 } from "./lib/auth0";

const MAINTENANCE_PATH = "/maintenance";

function isMaintenanceMode() {
  const value = (process.env.MAINTENANCE_MODE ?? "").trim().toLowerCase();
  return value === "1" || value === "true" || value === "on" || value === "yes";
}

export async function proxy(request) {
  const { pathname } = request.nextUrl;

  if (isMaintenanceMode()) {
    if (pathname === MAINTENANCE_PATH) return NextResponse.next();
    const url = request.nextUrl.clone();
    url.pathname = MAINTENANCE_PATH;
    url.search = "";
    return NextResponse.rewrite(url, {
      status: 503,
      headers: { "Retry-After": "600", "Cache-Control": "no-store" },
    });
  }

  if (pathname === MAINTENANCE_PATH) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  const authResponse = await auth0.middleware(request);

  // Always return the auth response.
  //
  // Note: The auth response forwards requests to your app routes by default.
  // If you need to block requests, do it before calling auth0.middleware() or
  // copy the authResponse headers except for x-middleware-next to your blocking response.
  return authResponse;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|manifest.webmanifest|opengraph-image|.*\\.(?:png|ico|svg|jpg|jpeg|webp)$).*)",
  ],
};
