import { cn } from "cn";

/** The glow behind the top of a page. `hero` adds the ruled grid and pulls
 *  the light to the right, behind the landing page's demo. */
export default function Backdrop({
  variant = "page",
  className,
}: {
  variant?: "page" | "hero";
  className?: string;
}) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-x-0 top-0 overflow-hidden",
        variant === "hero" ? "h-[900px]" : "h-[520px]",
        className,
      )}
    >
      {variant === "hero" && <div className="gridlines absolute inset-0" />}
      <div
        className={cn(
          "absolute rounded-full blur-2xl",
          variant === "hero"
            ? "top-[-200px] right-[-100px] h-[700px] w-[900px] bg-[radial-gradient(closest-side,rgb(91_91_255/.25),rgb(61_214_245/.08)_55%,transparent)]"
            : "top-[-300px] left-1/2 h-[560px] w-[1000px] -translate-x-1/2 bg-[radial-gradient(closest-side,rgb(91_91_255/.16),rgb(61_214_245/.05)_55%,transparent)]",
        )}
      />
    </div>
  );
}
