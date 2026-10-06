import assert from "node:assert/strict";
import test from "node:test";
import {
  DELETE_CONFIRMATION,
  apiErrorDetail,
  exportFilename,
  isDeleteConfirmed,
  isRevokedByDeletion,
} from "./account.ts";

test("deletion unlocks only on the exact confirmation word", () => {
  assert.equal(DELETE_CONFIRMATION, "DELETE");
  assert.equal(isDeleteConfirmed("DELETE"), true);
  assert.equal(isDeleteConfirmed("  DELETE "), true);
  for (const typed of ["", "delete", "Delete", "DELET", "DELETE ME", "D E L E T E"]) {
    assert.equal(isDeleteConfirmed(typed), false, typed);
  }
});

test("export file name uses the UTC date, like the API's header", () => {
  assert.equal(
    exportFilename(new Date("2026-10-06T23:30:00Z")),
    "resland-data-2026-10-06.zip",
  );
  assert.equal(
    exportFilename(new Date("2026-01-02T00:00:00Z")),
    "resland-data-2026-01-02.zip",
  );
});

test("apiErrorDetail reads FastAPI's string detail", () => {
  assert.equal(
    apiErrorDetail(JSON.stringify({ detail: "Something is still running." })),
    "Something is still running.",
  );
});

test("apiErrorDetail ignores bodies that aren't a string detail", () => {
  for (const body of [
    "",
    "<html><body>502 Bad Gateway</body></html>",
    JSON.stringify({ detail: { code: "x", message: "structured" } }),
    JSON.stringify({ message: "no detail" }),
    JSON.stringify({ detail: "   " }),
    "null",
  ]) {
    assert.equal(apiErrorDetail(body), null, body);
  }
});

test("every session is revoked while Auth0 still has the deleted login", () => {
  const now = Math.floor(Date.now() / 1000);
  assert.equal(isRevokedByDeletion(now + 3600, null), true);
  assert.equal(isRevokedByDeletion(undefined, null), true);
});

test("after Auth0 deleted the login, only older sessions are revoked", () => {
  const deletedAt = new Date("2026-10-01T12:00:00.750Z");
  const deletedSec = Math.floor(deletedAt.getTime() / 1000);
  // Signed in before (or in the same second as) the deletion: the old account.
  assert.equal(isRevokedByDeletion(deletedSec - 86400, deletedAt), true);
  assert.equal(isRevokedByDeletion(deletedSec, deletedAt), true);
  // A sign-up afterwards with the same social login is a new account.
  assert.equal(isRevokedByDeletion(deletedSec + 1, deletedAt), false);
  // No creation time on the session: treat it as old.
  assert.equal(isRevokedByDeletion(undefined, deletedAt), true);
});
