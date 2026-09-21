import { Auth0Client } from "@auth0/nextjs-auth0/server";

import { getBaseUrl } from "./base-url";

export const auth0 = new Auth0Client({
  appBaseUrl: getBaseUrl(),
  authorizationParameters: {
    audience: process.env.AUTH0_AUDIENCE,
  },
});
