export const getBaseUrl = (): string => {
  // 1. In the browser, use the current origin.
  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  // 2. Explicit override (e.g. custom domain or local tunnel).
  if (process.env.APP_BASE_URL) {
    return process.env.APP_BASE_URL;
  }

  // 3. On Vercel: production domain in production, otherwise the deployment URL.
  // NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL is set on previews too, so it is
  // only used when VERCEL_ENV is "production".
  if (
    process.env.VERCEL_ENV === "production" &&
    process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL
  ) {
    return `https://${process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL}`;
  }

  if (process.env.NEXT_PUBLIC_VERCEL_URL) {
    return `https://${process.env.NEXT_PUBLIC_VERCEL_URL}`;
  }

  // 4. Local development.
  return `http://localhost:${process.env.PORT ?? 3000}`;
};
