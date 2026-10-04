// Runs every DSA study center example in every language whose toolchain is
// on PATH, and checks each prints its expected.txt. Kept out of `pnpm test`
// because it compiles a few hundred programs: run `pnpm test:dsa-examples`.
//
//   DSA_ONLY=heaps,tries   only these topic slugs
//   DSA_LANGS=go,python    only these languages
//
// A language whose toolchain is missing is skipped, not failed — say so when
// you report results.
import assert from "node:assert/strict";
import { execFile, spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { availableParallelism } from "node:os";
import { join } from "node:path";
import { describe, test } from "node:test";
import { promisify } from "node:util";
import { DSA_LANGUAGES } from "./dsa.ts";
import { DSA_TOPICS } from "../content/dsa/index.ts";

const run = promisify(execFile);
const CONTENT_DIR = new URL("../content/dsa/", import.meta.url).pathname;

const RUNNERS = {
  // Node runs .ts directly by stripping the types.
  typescript: { bin: "node", probe: ["--version"], args: (f) => [f] },
  python: { bin: "python3", probe: ["--version"], args: (f) => [f] },
  go: { bin: "go", probe: ["version"], args: (f) => ["run", f] },
  // .NET 10 file-based apps. dotnet run prints compiler warnings to stdout,
  // but only when it rebuilds, so make any warning fail every run instead.
  csharp: {
    bin: "dotnet",
    probe: ["--version"],
    args: (f) => ["run", "-p:TreatWarningsAsErrors=true", f],
  },
  // JDK 11+ single-file source launch.
  java: { bin: "java", probe: ["-version"], args: (f) => [f] },
};

const ENV = {
  ...process.env,
  DOTNET_CLI_TELEMETRY_OPTOUT: "1",
  DOTNET_NOLOGO: "1",
  DOTNET_SKIP_FIRST_TIME_EXPERIENCE: "1",
  PYTHONDONTWRITEBYTECODE: "1",
};

function available(lang) {
  const { bin, probe } = RUNNERS[lang];
  return spawnSync(bin, probe, { env: ENV, stdio: "ignore" }).status === 0;
}

/** Folds the cosmetic differences between languages' default printing —
 *  `[0, 1]` (Python/Java), `[0 1]` (Go), `[0,1]` (JSON), `True` — so one
 *  expected.txt can serve all five. Anything beyond that must match. */
export function normalizeOutput(text) {
  return text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) =>
      line
        .replace(/["']/g, "")
        .replace(/\bTrue\b/g, "true")
        .replace(/\bFalse\b/g, "false")
        .replace(/\bNone\b|<nil>|\bnil\b/g, "null")
        .replace(/,\s*/g, " ")
        .replace(/\s+/g, " ")
        .replace(/([[({])\s+/g, "$1")
        .replace(/\s+([\])}])/g, "$1")
        .trim(),
    )
    .join("\n")
    .trim();
}

const only = process.env.DSA_ONLY?.split(",").filter(Boolean);
const onlyLangs = process.env.DSA_LANGS?.split(",").filter(Boolean);
const topics = DSA_TOPICS.filter((t) => !only || only.includes(t.slug));
const languages = DSA_LANGUAGES.filter(
  (l) => !onlyLangs || onlyLangs.includes(l.id),
);
const hasToolchain = Object.fromEntries(
  languages.map((l) => [l.id, available(l.id)]),
);
// gofmt rejects an empty file, so probe with the smallest valid one.
const hasGofmt = spawnSync("gofmt", [], { input: "package main\n" }).status === 0;

test("normalizeOutput folds per-language list and boolean printing", () => {
  const expected = normalizeOutput("[0, 1]\ntrue\n[[1, 2], [3]]\nabc");
  for (const variant of [
    "[0 1]\ntrue\n[[1 2] [3]]\nabc\n",
    "[0,1]\ntrue\n[[1,2],[3]]\nabc",
    "[ 0, 1 ]\r\nTrue\r\n[ [ 1, 2 ], [ 3 ] ]\r\n'abc'",
  ]) {
    assert.equal(normalizeOutput(variant), expected);
  }
  assert.notEqual(normalizeOutput("[0, 1]"), normalizeOutput("[1, 0]"));
  assert.notEqual(normalizeOutput("[0, 12]"), normalizeOutput("[01, 2]"));
});

describe("dsa examples", { concurrency: availableParallelism() }, () => {
  for (const topic of topics) {
    for (const example of [topic.template, ...topic.problems]) {
      const dir = join(CONTENT_DIR, topic.slug, example.id);
      const expectedFile = join(dir, "expected.txt");
      const expected = existsSync(expectedFile)
        ? normalizeOutput(readFileSync(expectedFile, "utf8"))
        : null;
      for (const lang of languages) {
        const name = `${topic.slug}/${example.id} [${lang.id}]`;
        const skip = hasToolchain[lang.id]
          ? false
          : `${RUNNERS[lang.id].bin} not on PATH`;
        test(name, { skip, timeout: 180_000 }, async () => {
          assert.ok(expected !== null, `missing ${topic.slug}/${example.id}/expected.txt`);
          const { bin, args } = RUNNERS[lang.id];
          let stdout;
          try {
            ({ stdout } = await run(bin, args(lang.file), {
              cwd: dir,
              env: ENV,
              timeout: 170_000,
              maxBuffer: 4 * 1024 * 1024,
            }));
          } catch (error) {
            assert.fail(
              `${name} exited with an error:\n${error.stdout ?? ""}${error.stderr ?? error.message}`,
            );
          }
          assert.equal(normalizeOutput(stdout), expected, `${name} output`);

          if (lang.id === "go" && hasGofmt) {
            const { stdout: unformatted } = await run("gofmt", ["-l", lang.file], {
              cwd: dir,
            });
            assert.equal(unformatted.trim(), "", `${name} isn't gofmt-formatted`);
          }
        });
      }
    }
  }
});
