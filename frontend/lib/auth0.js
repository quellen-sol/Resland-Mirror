import { Auth0Client } from "@auth0/nextjs-auth0/server";

// Vercel preview deployments serve each branch/deployment on a dynamic host,
// so a fixed APP_BASE_URL would send auth callbacks to the wrong origin. With
// no base URL configured, the SDK infers it from each request's host
// (x-forwarded-host/host + proto); Auth0's Allowed Callback/Logout URLs remain
// the allow-list for which hosts may complete auth.
if (process.env.VERCEL_ENV === "preview") {
  delete process.env.APP_BASE_URL;
}

export const auth0 = new Auth0Client({
  authorizationParameters: {
    audience: process.env.AUTH0_AUDIENCE,
  },
});
