"use client";

import { useLayoutEffect, useSyncExternalStore } from "react";
import { cn } from "cn";
import {
  DEFAULT_DSA_LANGUAGE,
  DSA_LANGUAGES,
  DSA_LANGUAGE_STORAGE_KEY,
  coerceDsaLanguage,
  type DsaLanguage,
} from "@/lib/dsa";

// The chosen language lives in data-dsa-lang on the layout's [data-dsa-root]
// wrapper, so CSS in globals.css can show the right code panel before React
// hydrates. This keeps React in step.

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function dsaRoot() {
  return document.querySelector<HTMLElement>("[data-dsa-root]");
}

function currentLanguage(): DsaLanguage {
  return coerceDsaLanguage(dsaRoot()?.dataset.dsaLang);
}

function setDsaLanguage(lang: DsaLanguage) {
  const root = dsaRoot();
  if (root) root.dataset.dsaLang = lang;
  try {
    localStorage.setItem(DSA_LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // Storage blocked: the choice still holds until the next full load.
  }
  for (const listener of listeners) listener();
}

function useDsaLanguage() {
  return useSyncExternalStore(
    subscribe,
    currentLanguage,
    () => DEFAULT_DSA_LANGUAGE,
  );
}

/** The layout's inline script covers full page loads. This covers arriving
 *  at /dsa through a client-side navigation, where that script never runs. */
export function DsaLanguageSync() {
  useLayoutEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(DSA_LANGUAGE_STORAGE_KEY);
    } catch {
      return;
    }
    if (stored && stored !== dsaRoot()?.dataset.dsaLang) {
      setDsaLanguage(coerceDsaLanguage(stored));
    }
  }, []);
  return null;
}

/** One button per language. Every picker on the page moves together. With
 *  `panelIdPrefix` it's a tab list for the panels `${prefix}-${language}`;
 *  without, a plain radio group that sets the preference. */
export function LanguageTabs({
  label,
  panelIdPrefix,
  className,
}: {
  label: string;
  panelIdPrefix?: string;
  className?: string;
}) {
  const current = useDsaLanguage();
  const asTabs = panelIdPrefix !== undefined;

  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const i = DSA_LANGUAGES.findIndex((l) => l.id === current);
    const next = DSA_LANGUAGES[(i + step + DSA_LANGUAGES.length) % DSA_LANGUAGES.length];
    setDsaLanguage(next.id);
    event.currentTarget
      .querySelector<HTMLButtonElement>(`[data-dsa-tab="${next.id}"]`)
      ?.focus();
  }

  return (
    <div
      role={asTabs ? "tablist" : "radiogroup"}
      aria-label={label}
      onKeyDown={onKeyDown}
      className={cn("flex flex-wrap gap-1", className)}
    >
      {DSA_LANGUAGES.map((lang) => {
        const selected = lang.id === current;
        return (
          <button
            key={lang.id}
            type="button"
            data-dsa-tab={lang.id}
            role={asTabs ? "tab" : "radio"}
            aria-selected={asTabs ? selected : undefined}
            aria-checked={asTabs ? undefined : selected}
            aria-controls={asTabs ? `${panelIdPrefix}-${lang.id}` : undefined}
            tabIndex={selected ? 0 : -1}
            onClick={() => setDsaLanguage(lang.id)}
            className="rounded-md px-2.5 py-1 text-xs font-medium text-zinc-400 transition-colors hover:bg-zinc-800/60 hover:text-zinc-200"
          >
            {lang.label}
          </button>
        );
      })}
    </div>
  );
}
