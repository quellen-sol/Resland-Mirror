import assert from "node:assert/strict";
import test from "node:test";
import { getDashboardMenuItems } from "./dashboard-menu.ts";

test("non-admin menu omits the admin link but keeps every other item", () => {
  const keys = getDashboardMenuItems(false).map((i) => i.key);
  assert.deepEqual(keys, [
    "upload",
    "tailor",
    "export",
    "edit-profile",
    "billing",
    "sign-out",
  ]);
});

test("admin menu inserts the admin link between export and edit-profile", () => {
  const keys = getDashboardMenuItems(true).map((i) => i.key);
  assert.deepEqual(keys, [
    "upload",
    "tailor",
    "export",
    "admin",
    "edit-profile",
    "billing",
    "sign-out",
  ]);
});

test("every navigational item carries an href", () => {
  for (const item of getDashboardMenuItems(true)) {
    if (item.key === "upload" || item.key === "export") continue;
    assert.match(item.href ?? "", /^\//, `${item.key} should link somewhere`);
  }
});
