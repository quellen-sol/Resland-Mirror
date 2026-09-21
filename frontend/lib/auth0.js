import { Auth0Client } from "@auth0/nextjs-auth0/server";

// On Vercel preview deployments the host is per-deployment, so the SDK must
// infer the base URL from each request rather than use the production
// APP_BASE_URL. The SDK falls back to the env var whenever `appBaseUrl` is
// undefined, so the var itself has to go. Auth0's Allowed Callback/Logout
// URLs gate which hosts may complete login.
if (process.env.VERCEL_ENV === "preview") {
  delete process.env.APP_BASE_URL;
}

export const auth0 = new Auth0Client({
  authorizationParameters: {
    audience: process.env.AUTH0_AUDIENCE,
  },
});
