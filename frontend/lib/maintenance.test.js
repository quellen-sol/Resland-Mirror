import assert from "node:assert/strict";
import test from "node:test";
import { isOpenDuringMaintenance } from "./maintenance.ts";

test("public pages and auth routes stay open during maintenance", () => {
  for (const path of ["/", "/help", "/auth/login", "/auth/callback", "/auth/logout"]) {
    assert.equal(isOpenDuringMaintenance(path), true, path);
  }
});

test("the signed-in app and API routes are gated during maintenance", () => {
  for (const path of [
    "/dashboard",
    "/onboarding",
    "/admin",
    "/billing",
    "/tailor",
    "/tailored/abc",
    "/api/admin/settings",
    "/api/site-settings",
    "/some-unknown-page",
  ]) {
    assert.equal(isOpenDuringMaintenance(path), false, path);
  }
});

test("gating matches whole paths, not prefixes", () => {
  assert.equal(isOpenDuringMaintenance("/helpful"), false);
  assert.equal(isOpenDuringMaintenance("/help/extra"), false);
  assert.equal(isOpenDuringMaintenance("/authors"), false);
});
