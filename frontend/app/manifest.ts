import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Resland",
    short_name: "Resland",
    description: "AI resume tailoring and interview prep for software engineers",
    start_url: "/",
    display: "standalone",
    theme_color: "#09090b",
    background_color: "#09090b",
    icons: [
      {
        src: "/android-chrome-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/android-chrome-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
