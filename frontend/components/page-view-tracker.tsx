"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { isTrackedPath, normalizePath, type PageViewBeacon } from "@/lib/traffic";

const ENDPOINT = "/api/metrics/pageview";
// Per tab, so a visit ends when the tab closes. No cookie involved.
const VISIT_KEY = "resland.visit";
const LAST_PATH_KEY = "resland.visit.path";

// Development renders effects twice; don't count that as two views.
let lastSent = { path: "", at: 0 };

function send(beacon: PageViewBeacon) {
  const body = JSON.stringify(beacon);
  const queued = navigator.sendBeacon?.(
    ENDPOINT,
    new Blob([body], { type: "application/json" }),
  );
  if (!queued) {
    void fetch(ENDPOINT, {
      method: "POST",
      body,
      keepalive: true,
      headers: { "Content-Type": "application/json" },
    }).catch(() => {});
  }
}

/** Records a page view on every page load and client-side navigation, for
 *  the Traffic panel in /admin. See lib/traffic.ts for what's stored. */
export default function PageViewTracker() {
  const pathname = usePathname();

  useEffect(() => {
    const path = normalizePath(pathname);
    if (!path || !isTrackedPath(path) || navigator.webdriver) return;
    const now = Date.now();
    if (lastSent.path === path && now - lastSent.at < 1000) return;
    lastSent = { path, at: now };

    try {
      let visit = sessionStorage.getItem(VISIT_KEY);
      const prev = sessionStorage.getItem(LAST_PATH_KEY);
      const beacon: PageViewBeacon = { visit: visit ?? crypto.randomUUID(), path };
      if (visit && prev) {
        beacon.prev = prev;
      } else {
        visit = beacon.visit;
        sessionStorage.setItem(VISIT_KEY, visit);
        const params = new URLSearchParams(location.search);
        if (document.referrer) beacon.referrer = document.referrer;
        beacon.utm_source = params.get("utm_source") ?? undefined;
        beacon.utm_campaign = params.get("utm_campaign") ?? undefined;
      }
      sessionStorage.setItem(LAST_PATH_KEY, path);
      send(beacon);
    } catch {
      // Storage blocked (some privacy modes): skip rather than miscount.
    }
  }, [pathname]);

  return null;
}
