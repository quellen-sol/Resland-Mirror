// The share card behind every opengraph-image route: the logo, an eyebrow,
// a big title and an optional subtitle on the site's dark background.
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";

export const OG_SIZE = { width: 1200, height: 630 };
export const OG_CONTENT_TYPE = "image/png";

// The 192px icon is plenty at this size and keeps each card small.
const logo = readFile(join(process.cwd(), "public/android-chrome-192x192.png"), "base64").then(
  (data) => `data:image/png;base64,${data}`,
);

export async function ogCard({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "64px 72px",
          background: "#08080b",
          backgroundImage:
            "radial-gradient(circle at 88% 0%, rgba(123,123,255,0.35), transparent 55%), radial-gradient(circle at 0% 100%, rgba(61,214,245,0.16), transparent 50%)",
          color: "#fafafa",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          {/* eslint-disable-next-line @next/next/no-img-element -- ImageResponse renders plain <img> */}
          <img src={await logo} width={56} height={56} alt="" />
          <span style={{ fontSize: 34 }}>Resland</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
          <span
            style={{ fontSize: 24, letterSpacing: 3, textTransform: "uppercase", color: "#a9a9ff" }}
          >
            {eyebrow}
          </span>
          <span
            style={{
              fontSize: title.length > 44 ? 62 : 76,
              lineHeight: 1.08,
              letterSpacing: -2,
            }}
          >
            {title}
          </span>
          {subtitle && (
            <span style={{ fontSize: 30, lineHeight: 1.35, color: "#a1a1aa" }}>{subtitle}</span>
          )}
        </div>
        <span style={{ fontSize: 24, color: "#71717a" }}>resland.org</span>
      </div>
    ),
    OG_SIZE,
  );
}
