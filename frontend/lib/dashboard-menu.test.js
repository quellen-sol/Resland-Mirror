import assert from "node:assert/strict";
import test from "node:test";
import { getDashboardMenuItems } from "./dashboard-menu.ts";

test("non-admin menu omits the admin link but keeps every other item", () => {
  const keys = getDashboardMenuItems(false).map((i) => i.key);
  assert.deepEqual(keys, [
    "upload",
    "tailor",
    "tailored",
    "system-design",
    "dsa",
    "export",
    "edit-profile",
    "billing",
    "account",
    "help",
    "sign-out",
  ]);
});

test("admin menu inserts the admin link between export and edit-profile", () => {
  const keys = getDashboardMenuItems(true).map((i) => i.key);
  assert.deepEqual(keys, [
    "upload",
    "tailor",
    "tailored",
    "system-design",
    "dsa",
    "export",
    "admin",
    "edit-profile",
    "billing",
    "account",
    "help",
    "sign-out",
  ]);
});

test("every navigational item carries an href", () => {
  for (const item of getDashboardMenuItems(true)) {
    if (item.key === "upload" || item.key === "export") continue;
    assert.match(item.href ?? "", /^\//, `${item.key} should link somewhere`);
  }
});

test("the account page is reachable from the menu", () => {
  const item = getDashboardMenuItems(false).find((i) => i.key === "account");
  assert.equal(item?.href, "/account");
});
