"use client";

import { useEffect, useRef, type ComponentProps } from "react";

/** A <section> that fades up the first time it scrolls into view. The hiding
 *  is CSS-gated on scripting and motion preferences (see globals.css). */
export default function Reveal(props: ComponentProps<"section">) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        el.dataset.reveal = "shown";
        io.disconnect();
      },
      { threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return <section ref={ref} data-reveal="" {...props} />;
}
