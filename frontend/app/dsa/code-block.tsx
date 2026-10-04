import CopyButton from "@/components/copy-button";
import type { DsaExample } from "@/lib/dsa";
import { loadExampleCode } from "@/lib/dsa-code";
import { LanguageTabs } from "./language";

/** An example's solution in every language. All five panels are in the HTML
 *  (CSS shows the chosen one), so switching never waits on the network. */
export default async function CodeBlock({
  topicSlug,
  example,
}: {
  topicSlug: string;
  example: DsaExample;
}) {
  const samples = await loadExampleCode(topicSlug, example.id);
  const panelIdPrefix = `${example.id}-code`;

  return (
    <div className="edge overflow-hidden rounded-xl border border-white/[.08] bg-zinc-950/70">
      <div className="flex items-center gap-2 border-b border-white/[.06] px-2 py-1.5">
        <LanguageTabs
          label={`${example.title} solution language`}
          panelIdPrefix={panelIdPrefix}
        />
      </div>
      {samples.map((sample) => (
        <div
          key={sample.language}
          id={`${panelIdPrefix}-${sample.language}`}
          role="tabpanel"
          aria-label={`${example.title} in ${sample.label}`}
          data-dsa-panel={sample.language}
          className="relative"
        >
          <CopyButton
            text={sample.code}
            className="absolute top-3 right-3 rounded-md bg-zinc-900/80 p-1.5"
          />
          <div
            className="dsa-code overflow-x-auto text-[13px] leading-6 [&_code]:font-mono [&_pre]:w-fit [&_pre]:min-w-full [&_pre]:[tab-size:4] [&_pre]:p-4 [&_pre]:pr-12"
            dangerouslySetInnerHTML={{ __html: sample.html }}
          />
        </div>
      ))}
    </div>
  );
}
