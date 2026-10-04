import { readFile } from "node:fs/promises";
import path from "node:path";
import { createHighlighter, type Highlighter } from "shiki";
import { DSA_LANGUAGES, type DsaLanguage } from "./dsa";

// Server-only: reads an example's solution files from content/dsa and
// highlights them. Topic pages are prerendered, so this runs at build time.

const THEME = "github-dark-default";

const GRAMMARS: Record<DsaLanguage, string> = {
  typescript: "typescript",
  python: "python",
  go: "go",
  csharp: "csharp",
  java: "java",
};

let highlighter: Promise<Highlighter> | null = null;

function getHighlighter() {
  highlighter ??= createHighlighter({
    themes: [THEME],
    langs: Object.values(GRAMMARS),
  });
  return highlighter;
}

export interface DsaCodeSample {
  language: DsaLanguage;
  label: string;
  code: string;
  /** Highlighted <pre> from shiki. */
  html: string;
}

/** Every language's solution for one example, in tab order. */
export async function loadExampleCode(
  topicSlug: string,
  exampleId: string,
): Promise<DsaCodeSample[]> {
  const dir = path.join(process.cwd(), "content", "dsa", topicSlug, exampleId);
  const shiki = await getHighlighter();
  return Promise.all(
    DSA_LANGUAGES.map(async (lang) => {
      const code = (await readFile(path.join(dir, lang.file), "utf8")).trimEnd();
      return {
        language: lang.id,
        label: lang.label,
        code,
        html: shiki.codeToHtml(code, { lang: GRAMMARS[lang.id], theme: THEME }),
      };
    }),
  );
}
