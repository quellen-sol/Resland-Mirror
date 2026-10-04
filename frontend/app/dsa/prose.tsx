import Link from "next/link";
import { Lightbulb } from "lucide-react";
import { cn } from "cn";
import { parseInline, type DsaBlock } from "@/lib/dsa";

const linkClass =
  "text-brand-300 underline underline-offset-4 hover:text-brand-200";

/** One line of prose with its `code`, **bold** and [links](...) rendered. */
export function Inline({ text }: { text: string }) {
  return parseInline(text).map((token, i) => {
    switch (token.type) {
      case "code":
        return (
          <code
            key={i}
            className="rounded bg-white/[.06] px-1 py-px font-mono text-[0.88em] text-brand-100"
          >
            {token.text}
          </code>
        );
      case "strong":
        return (
          <strong key={i} className="font-semibold text-zinc-100">
            {token.text}
          </strong>
        );
      case "link":
        return token.href.startsWith("/") ? (
          <Link key={i} href={token.href} className={linkClass}>
            {token.text}
          </Link>
        ) : (
          <a
            key={i}
            href={token.href}
            target="_blank"
            rel="noreferrer"
            className={linkClass}
          >
            {token.text}
          </a>
        );
      default:
        return token.text;
    }
  });
}

export function Blocks({
  blocks,
  className,
}: {
  blocks: DsaBlock[];
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {blocks.map((block, i) => {
        switch (block.type) {
          case "p":
            return (
              <p key={i} className="leading-7 text-zinc-300">
                <Inline text={block.text} />
              </p>
            );
          case "list": {
            const List = block.ordered ? "ol" : "ul";
            return (
              <List
                key={i}
                className={cn(
                  "flex flex-col gap-2 pl-5 leading-7 text-zinc-300 marker:text-zinc-500",
                  block.ordered ? "list-decimal" : "list-disc",
                )}
              >
                {block.items.map((item, j) => (
                  <li key={j} className="pl-1">
                    <Inline text={item} />
                  </li>
                ))}
              </List>
            );
          }
          case "diagram":
            return (
              <figure key={i} className="flex flex-col gap-2">
                <pre className="overflow-x-auto rounded-lg border border-white/[.08] bg-zinc-950/70 p-4 font-mono text-[13px] leading-5 text-zinc-300">
                  {block.text}
                </pre>
                {block.caption && (
                  <figcaption className="text-xs text-zinc-500">
                    <Inline text={block.caption} />
                  </figcaption>
                )}
              </figure>
            );
          case "tip":
            return (
              <aside
                key={i}
                className="flex gap-3 rounded-lg border border-brand-500/25 bg-brand-500/[.06] px-4 py-3 text-sm leading-6 text-zinc-300"
              >
                <Lightbulb className="mt-1 size-4 shrink-0 text-brand-300" aria-hidden />
                <p>
                  <Inline text={block.text} />
                </p>
              </aside>
            );
        }
      })}
    </div>
  );
}
