import assert from "node:assert/strict";
import test from "node:test";
import {
  DELETE_CONFIRMATION,
  apiErrorDetail,
  exportFilename,
  isDeleteConfirmed,
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
