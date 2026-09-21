import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

// lib/auth0.js mutates process.env at module load, so each case runs in a
// fresh subprocess.
const frontendDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

const dummyAuth0Env = {
  AUTH0_DOMAIN: "example.auth0.com",
  AUTH0_CLIENT_ID: "client-id",
  AUTH0_CLIENT_SECRET: "client-secret",
  AUTH0_SECRET: "a".repeat(64),
  AUTH0_AUDIENCE: "audience",
};

const appBaseUrlAfterImport = ({ env, unset = [] }) => {
  const childEnv = { ...process.env, ...dummyAuth0Env, ...env };
  for (const key of unset) delete childEnv[key];
  const result = spawnSync(
    process.execPath,
    [
      "-e",
      'import("./lib/auth0.js").then(() => console.log(process.env.APP_BASE_URL ?? "UNSET"))',
    ],
    { cwd: frontendDir, env: childEnv, encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim().split("\n").at(-1);
};

test("deletes APP_BASE_URL on Vercel preview deployments so the SDK infers the request host", () => {
  const out = appBaseUrlAfterImport({
    env: { VERCEL_ENV: "preview", APP_BASE_URL: "https://resland.org" },
  });
  assert.equal(out, "UNSET");
});

test("keeps APP_BASE_URL on Vercel production deployments", () => {
  const out = appBaseUrlAfterImport({
    env: { VERCEL_ENV: "production", APP_BASE_URL: "https://resland.org" },
  });
  assert.equal(out, "https://resland.org");
});

test("keeps APP_BASE_URL outside Vercel", () => {
  const out = appBaseUrlAfterImport({
    env: { APP_BASE_URL: "https://resland.org" },
    unset: ["VERCEL_ENV"],
  });
  assert.equal(out, "https://resland.org");
});
