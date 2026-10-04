import Image from "next/image";
import Link from "next/link";
import Backdrop from "@/components/backdrop";
import InlineScript from "@/components/inline-script";
import SiteFooter from "@/components/site-footer";
import { Toaster } from "@/components/ui/sonner";
import { DSA_LANGUAGES, DSA_LANGUAGE_STORAGE_KEY } from "@/lib/dsa";
import HeaderLinks from "./header-links";
import { DsaLanguageSync } from "./language";
import { DsaProgressProvider } from "./progress";

// Apply the saved code language to the wrapper before first paint so the
// right panels show without a flash. See the [data-dsa-lang] rules in
// globals.css.
const LANGUAGE_SCRIPT = `try{var l=localStorage.getItem(${JSON.stringify(
  DSA_LANGUAGE_STORAGE_KEY,
)});if(${JSON.stringify(DSA_LANGUAGES.map((x) => x.id))}.indexOf(l)>-1)document.currentScript.parentElement.dataset.dsaLang=l}catch(e){}`;

export default function DsaLayout({ children }: { children: React.ReactNode }) {
  return (
    <DsaProgressProvider>
      {/* The script sets data-dsa-lang here before React hydrates, so this
          element (and only this one) ignores the attribute mismatch. */}
      <div data-dsa-root="" suppressHydrationWarning className="flex flex-1 flex-col">
        <InlineScript html={LANGUAGE_SCRIPT} />
        <DsaLanguageSync />
        <div className="relative flex flex-1 flex-col overflow-x-clip">
          <Backdrop />
          <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-5">
            <div className="flex min-w-0 items-center gap-2.5 text-[15px] font-semibold tracking-tight">
              <Link href="/" className="flex shrink-0 items-center gap-2.5">
                <Image src="/resland-logo.png" alt="" width={28} height={28} /> Resland
              </Link>
              <span aria-hidden className="text-zinc-700">
                /
              </span>
              <Link href="/dsa" className="truncate text-zinc-300 hover:text-white">
                DSA Study Center
              </Link>
            </div>
            <HeaderLinks />
          </header>
          {children}
        </div>
        <SiteFooter />
        <Toaster theme="dark" richColors position="bottom-right" />
      </div>
    </DsaProgressProvider>
  );
}
