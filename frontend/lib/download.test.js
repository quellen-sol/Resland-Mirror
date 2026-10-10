import assert from "node:assert/strict";
import test from "node:test";
import { filenameFromContentDisposition } from "./download.ts";

const FALLBACK = "download.bin";

test("reads a quoted filename", () => {
  assert.equal(
    filenameFromContentDisposition(
      'attachment; filename="resland-data-2026-10-06.zip"',
      FALLBACK,
    ),
    "resland-data-2026-10-06.zip",
  );
});

test("reads a bare filename", () => {
  assert.equal(
    filenameFromContentDisposition("attachment; filename=data.zip", FALLBACK),
    "data.zip",
  );
});

test("prefers the RFC 5987 filename* form", () => {
  assert.equal(
    filenameFromContentDisposition(
      "attachment; filename=\"plain.zip\"; filename*=UTF-8''my%20data.zip",
      FALLBACK,
    ),
    "my data.zip",
  );
});

test("drops directory parts", () => {
  assert.equal(
    filenameFromContentDisposition(
      'attachment; filename="../../etc/data.zip"',
      FALLBACK,
    ),
    "data.zip",
  );
});

test("falls back when there's nothing usable", () => {
  for (const header of [
    null,
    "",
    "attachment",
    'attachment; filename=""',
    "attachment; filename*=UTF-8''%E0%A4%A",
  ]) {
    assert.equal(filenameFromContentDisposition(header, FALLBACK), FALLBACK, String(header));
  }
});
