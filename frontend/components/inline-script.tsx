"use client";

/** A script that runs while the HTML is parsed, before first paint. React
 *  doesn't execute scripts it renders on the client, and warns about them in
 *  development, so the client render emits an inert text/plain copy. This has
 *  to be a client component for that switch to happen in the browser. */
export default function InlineScript({ html }: { html: string }) {
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
