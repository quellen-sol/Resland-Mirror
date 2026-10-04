import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowRight, Plus } from "lucide-react";
import { auth0 } from "@/lib/auth0";
import { getUser } from "@/lib/db";
import { getSiteSettings } from "@/lib/settings";
import Backdrop from "@/components/backdrop";
import SiteFooter from "@/components/site-footer";
import HowItWorks from "@/components/landing/how-it-works";
import LiveDemo from "@/components/landing/live-demo";
import Reveal from "@/components/landing/reveal";
import Spotlight from "@/components/landing/spotlight";

// Mirrors TOKEN_PACKS in backend/api/src/api/billing/model.py. The packs
// endpoint needs a signed-in user, so the landing page can't fetch them.
const PACKS = [
  { name: "Starter", pay: 5, get: 5 },
  { name: "Standard", pay: 10, get: 11 },
  { name: "Pro", pay: 20, get: 25 },
];

const QUESTION_CHIPS = [
  "How many people?",
  "What changed after?",
  "Roughly how much?",
  "Who used it?",
];

const faqs = [
  [
    "Will it change my resume without asking?",
    "No. Every suggestion is a proposal. You can accept it, ask for something different, or throw it out.",
  ],
  [
    "Which AI model does it use?",
    "There's a default, and you can switch models any time you ask for a suggestion or tailor a resume.",
  ],
  [
    "Who can see my resume?",
    "Your profile is private to your account. When you run a suggestion or tailor a resume, the text involved is sent to the AI model you picked so it can do the work.",
  ],
  [
    "What do I end up with?",
    "A Word file for your main resume, plus one for every tailored version you save.",
  ],
];

const card = "edge rounded-2xl border border-white/[.08] bg-card";
const eyebrow = "font-mono text-xs tracking-wider text-brand-400 uppercase";
const h2 = "text-4xl font-semibold tracking-[-0.03em]";

export default async function Home() {
  const { maintenance_mode } = await getSiteSettings();
  let session: Awaited<ReturnType<typeof auth0.getSession>> = null;
  let lookupFailed = false;
  let signedInTarget: string | null = null;
  try {
    session = await auth0.getSession();
    if (session) {
      const user = await getUser();
      // Admins can always view the landing page.
      if (user && !user.site_admin) signedInTarget = user.has_onboarded ? "/dashboard" : "/onboarding";
    }
  } catch {
    lookupFailed = true;
  }
  // redirect() works by throwing, so it must stay outside the try above or
  // the catch swallows it and signed-in users never leave the landing page.
  if (signedInTarget) redirect(signedInTarget);
  const primaryHref = lookupFailed || session ? "/dashboard" : "/auth/login?screen_hint=signup";
  const primaryLabel = lookupFailed || session ? "Go to Dashboard" : "Get Started";
  const jsonLd = [
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: "Resland",
      url: "https://resland.org",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      offers: { "@type": "Offer", priceCurrency: "USD", price: "0", description: "Pay-as-you-go credits" },
    },
    { "@context": "https://schema.org", "@type": "WebSite", name: "Resland", url: "https://resland.org" },
  ];

  return (
    <div className="relative flex flex-1 flex-col overflow-x-clip">
      <Backdrop variant="hero" />

      {maintenance_mode && (
        <p className="relative border-b border-red-800/60 bg-red-950/60 px-6 py-2.5 text-center text-sm text-red-200">
          Resland is down for maintenance, so the app is unavailable for now. Your data is safe. Check
          back soon.
        </p>
      )}

      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link href="/" className="flex items-center gap-2.5 text-[15px] font-semibold tracking-tight">
          <Image src="/resland-logo.png" alt="" width={28} height={28} preload /> Resland
        </Link>
        <nav aria-label="Sections" className="hidden items-center gap-8 text-sm text-zinc-400 md:flex">
          <a href="#how" className="hover:text-zinc-100">How it works</a>
          <a href="#pricing" className="hover:text-zinc-100">Pricing</a>
          <a href="#faq" className="hover:text-zinc-100">FAQ</a>
          <Link href="/dsa" className="hover:text-zinc-100">DSA Study Center</Link>
        </nav>
        <div className="flex items-center gap-1">
          <Link href="/auth/login?returnTo=/dashboard" className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white">
            Log In
          </Link>
          <Link href={primaryHref} className="rounded-lg bg-white px-3.5 py-1.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200">
            {primaryLabel}
          </Link>
        </div>
      </header>

      <main className="relative">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 pt-16 pb-12 lg:grid-cols-2 lg:pt-24">
          <div>
            <h1 className="text-[44px] leading-[0.98] font-semibold tracking-[-0.045em] sm:text-[62px]">
              <span className="rise block text-balance">A resume for every job.</span>
              <span className="rise block text-zinc-500 [animation-delay:.12s]">Nothing made up.</span>
            </h1>
            <p className="rise mt-7 max-w-md text-[17px] leading-7 text-zinc-400 [animation-delay:.24s]">
              Paste a job posting and Resland reorders and rewrites your experience to fit it. When a
              bullet is vague, it asks you for the details instead of guessing.
            </p>
            <div className="rise mt-9 flex flex-wrap gap-3 [animation-delay:.36s]">
              <Link
                href={primaryHref}
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-white px-6 text-[15px] font-medium text-zinc-950 shadow-[0_0_0_1px_rgba(255,255,255,.2),0_8px_30px_-6px_rgba(123,123,255,.55)] hover:bg-zinc-200"
              >
                {primaryLabel} <ArrowRight className="size-4" />
              </Link>
              <a
                href="#how"
                className="edge inline-flex h-11 items-center rounded-xl border border-white/10 bg-white/[.03] px-6 text-[15px] font-medium text-zinc-200 hover:bg-white/[.07]"
              >
                See how it works
              </a>
            </div>
            <p className="rise mt-5 font-mono text-xs text-zinc-500 [animation-delay:.48s]">
              No subscription · pay per use
            </p>
          </div>
          <div className="rise [animation-delay:.2s]">
            <LiveDemo />
          </div>
        </section>

        {/* How it works */}
        <Reveal id="how" aria-labelledby="how-heading" className="mx-auto max-w-6xl scroll-mt-8 px-6 pt-32">
          <p className={eyebrow}>How it works</p>
          <h2 id="how-heading" className={`mt-3 max-w-xl ${h2}`}>
            Three steps. You approve every change.
          </h2>
          <HowItWorks />
        </Reveal>

        {/* What you get */}
        <Reveal aria-labelledby="features-heading" className="mx-auto max-w-6xl px-6 pt-32">
          <h2 id="features-heading" className={`max-w-xl ${h2}`}>
            Built for people applying to more than one job.
          </h2>
          <div className="mt-12 grid gap-4 md:grid-cols-3">
            <Spotlight className={`${card} p-6 md:col-span-2`}>
              <h3 className="font-medium">It asks before it writes</h3>
              <p className="mt-1.5 max-w-md text-sm leading-6 text-zinc-400">
                When a bullet needs a number or an outcome, Resland asks you for it instead of guessing.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 text-sm">
                {QUESTION_CHIPS.map((q) => (
                  <span key={q} className="rounded-full border border-white/10 px-3 py-1 text-zinc-300">
                    {q}
                  </span>
                ))}
              </div>
            </Spotlight>
            <Spotlight className={`${card} p-6`}>
              <h3 className="font-medium">A version per job</h3>
              <p className="mt-1.5 text-sm leading-6 text-zinc-400">Every tailored copy is saved on its own.</p>
              <ul className="mt-5 divide-y divide-white/[.06] rounded-xl border border-white/[.08] text-sm">
                <li className="flex justify-between px-3 py-2">
                  <span>Platform Eng · Globex</span>
                  <span className="font-mono text-xs text-emerald-300">Exported</span>
                </li>
                <li className="flex justify-between px-3 py-2">
                  <span>SRE · Initech</span>
                  <span className="font-mono text-xs text-zinc-500">Saved</span>
                </li>
              </ul>
            </Spotlight>
            <Spotlight className={`${card} p-6`}>
              <h3 className="font-medium">Your pick of model</h3>
              <p className="mt-1.5 text-sm leading-6 text-zinc-400">
                Use the default or switch. You see pricing for each model before anything runs.
              </p>
            </Spotlight>
            <Spotlight className={`${card} p-6`}>
              <h3 className="font-medium">Word export</h3>
              <p className="mt-1.5 text-sm leading-6 text-zinc-400">
                Download any version as a .docx and tweak it before you send it.
              </p>
            </Spotlight>
            <Spotlight className={`${card} p-6`}>
              <h3 className="font-medium">Private</h3>
              <p className="mt-1.5 text-sm leading-6 text-zinc-400">
                Your profile is only visible to you. Payments go through Stripe.
              </p>
            </Spotlight>
          </div>
        </Reveal>

        {/* Pricing */}
        <Reveal id="pricing" aria-labelledby="pricing-heading" className="mx-auto max-w-6xl scroll-mt-8 px-6 pt-32">
          <Spotlight className="edge grid items-center gap-10 rounded-3xl border border-white/[.08] bg-card p-8 sm:p-12 md:grid-cols-[1.2fr_1fr]">
            <div>
              <p className={eyebrow}>Pricing</p>
              <h2 id="pricing-heading" className={`mt-3 ${h2}`}>
                Pay for what you use.
              </h2>
              <p className="mt-4 max-w-md leading-7 text-zinc-400">
                There&apos;s no subscription. Add balance when you need it, and each suggestion or
                tailoring run takes a little from it. Bigger packs come with bonus balance.
              </p>
            </div>
            <div className="rounded-2xl border border-white/[.08] bg-black/30 p-6">
              <p className="text-sm text-zinc-400">Balance packs</p>
              <ul className="mt-4 space-y-3 font-mono text-sm">
                {PACKS.map((p) => (
                  <li key={p.name} className="flex items-baseline justify-between gap-4">
                    <span className="text-zinc-300">
                      {p.name} <span className="text-zinc-500">· ${p.pay}</span>
                    </span>
                    <span className="text-zinc-100">
                      ${p.get.toFixed(2)}
                      {p.get > p.pay && (
                        <span className="ml-2 text-emerald-300">
                          +{Math.round(((p.get - p.pay) / p.pay) * 100)}%
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-5 text-xs text-zinc-500">One-time payments through Stripe. Nothing renews.</p>
            </div>
          </Spotlight>
        </Reveal>

        {/* FAQ */}
        <Reveal
          id="faq"
          aria-labelledby="faq-heading"
          className="mx-auto grid max-w-6xl scroll-mt-8 gap-10 px-6 pt-32 md:grid-cols-[1fr_1.6fr]"
        >
          <h2 id="faq-heading" className={h2}>
            Questions
          </h2>
          <div className="divide-y divide-white/[.08] border-y border-white/[.08]">
            {faqs.map(([question, answer], i) => (
              <details key={question} className="group py-5" open={i === 0}>
                <summary className="flex cursor-pointer list-none items-center justify-between gap-6 font-medium [&::-webkit-details-marker]:hidden">
                  {question}
                  <Plus className="size-4 shrink-0 text-zinc-500 transition-transform group-open:rotate-45" />
                </summary>
                <p className="mt-3 text-sm leading-6 text-zinc-400">{answer}</p>
              </details>
            ))}
            <p className="py-5 text-sm text-zinc-500">
              More in{" "}
              <Link href="/help" className="text-zinc-300 underline-offset-4 hover:underline">
                Help &amp; FAQ
              </Link>
              .
            </p>
          </div>
        </Reveal>

        {/* Closing CTA */}
        <Reveal className="mx-auto max-w-6xl px-6 py-32">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-400/50 via-white/10 to-brand-cyan/40 p-px">
            <div className="relative rounded-[23px] bg-card px-8 py-16 text-center">
              <div
                aria-hidden
                className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-48 w-[600px] max-w-full rounded-full bg-brand-400/20 blur-3xl"
              />
              <h2 className="relative text-4xl font-semibold tracking-[-0.03em] text-balance sm:text-5xl">
                Try it on the next job you apply for.
              </h2>
              <Link
                href={primaryHref}
                className="relative mt-8 inline-flex h-11 items-center gap-2 rounded-xl bg-white px-6 text-[15px] font-medium text-zinc-950 hover:bg-zinc-200"
              >
                {primaryLabel} <ArrowRight className="size-4" />
              </Link>
            </div>
          </div>
        </Reveal>
      </main>

      <SiteFooter
        links={[
          { href: "/auth/login", label: "Log In" },
          { href: "/auth/login?screen_hint=signup", label: "Sign Up" },
        ]}
      />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    </div>
  );
}
