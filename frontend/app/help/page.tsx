import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import SiteFooter from "@/components/site-footer";

export const metadata: Metadata = { title: "Help & FAQ" };

const SECTIONS: {
  title: string;
  faqs: [string, string][];
}[] = [
  {
    title: "Getting Started",
    faqs: [
      [
        "What is Resland?",
        "Resland keeps your resume as a structured profile — experience, skills, education, and projects — that you can polish with AI suggestions, tailor to specific job postings, and export as a document whenever you need it.",
      ],
      [
        "How do I set up my profile?",
        "When you first sign in, onboarding lets you upload an existing resume (we parse it into your profile automatically) or enter your information by hand. If you skipped onboarding, upload a resume or open Edit Profile from the dashboard menu.",
      ],
      [
        "What is the dashboard?",
        "The dashboard shows your base resume information — the version everything else builds on. Keep it current: it's what gets tailored to job postings, improved by suggestions, and re-exported.",
      ],
    ],
  },
  {
    title: "Suggestions & Tailoring",
    faqs: [
      [
        "What does the sparkle icon do?",
        "The sparkle next to a bullet or job opens an AI suggestion. The agent may ask a question or two, then proposes a rewrite you can accept or dismiss. You can also steer it with your own prompt.",
      ],
      [
        "How do I tailor my resume to a job?",
        "Open Tailor Resume from the dashboard menu and paste the job description. The agent rewrites and reorders your bullets to match it, then saves the result to your Tailored Resumes board where you can keep editing and export it.",
      ],
      [
        "Can I copy a bullet point?",
        "Yes — the copy icon next to each bullet on the dashboard copies its text to your clipboard.",
      ],
      [
        "Which AI model is used?",
        "You pick the model when starting a suggestion or tailoring run. Different models have different per-token prices — cheaper models cost less per run.",
      ],
    ],
  },
  {
    title: "Billing & Credits",
    faqs: [
      [
        "How does billing work?",
        "Resland is pay-as-you-go — no subscription. You buy balance in packs on the Billing page, and AI actions (suggestions and tailoring) draw from it. Bigger packs include bonus balance.",
      ],
      [
        "How much does each action cost?",
        "Cost is based on the tokens your chosen model uses, priced per 1K tokens. Exact amounts vary with resume length and the model you pick.",
      ],
      [
        "What if my balance runs out mid-run?",
        "A job that already started is never interrupted — the balance is deducted afterward and simply can't go below zero. You just need a positive balance to start something new.",
      ],
      [
        "How do purchases work?",
        "Checkout is handled securely by Stripe — Resland never sees your card details. Your balance usually tops up a few seconds after checkout, and every purchase appears in your purchase history.",
      ],
    ],
  },
  {
    title: "Your Account",
    faqs: [
      [
        "How do I update my information?",
        "Open Edit Profile from the dashboard menu to change your contact info, links, experience, education, projects, and skills. Everything there is what exports and tailoring read from.",
      ],
      [
        "Who can see my resume?",
        "Your profile is private to your account and isn't shared with other users.",
      ],
      [
        "What format are exports?",
        "Resumes export as editable DOCX documents so you can make final tweaks before sending them out.",
      ],
    ],
  },
];

export default function HelpPage() {
  return (
    <div className="relative flex flex-1 flex-col overflow-hidden bg-zinc-950 font-sans text-zinc-100">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5 sm:px-8">
        <Link
          href="/"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight"
        >
          <Image
            src="/resland-logo.png"
            alt="Resland"
            width={32}
            height={32}
            priority
            className="rounded-lg"
          />{" "}
          Resland
        </Link>
        <nav className="flex gap-4 text-sm text-zinc-400">
          <Link href="/dashboard" className="hover:text-zinc-200">
            Dashboard
          </Link>
          <Link href="/" className="hover:text-zinc-200">
            Home
          </Link>
        </nav>
      </header>
      <main className="relative mx-auto w-full max-w-3xl flex-1 px-6 pb-20 pt-10 sm:px-8">
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
          Help &amp; FAQ
        </h1>
        <p className="mt-2 text-sm text-zinc-400">
          Answers to common questions about profiles, AI features, and billing.
        </p>
        <div className="mt-10 flex flex-col gap-10">
          {SECTIONS.map((section) => (
            <section key={section.title} aria-labelledby={section.title}>
              <h2
                id={section.title}
                className="text-xl font-semibold text-zinc-100"
              >
                {section.title}
              </h2>
              <div className="mt-4 divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/60 px-5">
                {section.faqs.map(([question, answer]) => (
                  <details key={question} className="group py-4">
                    <summary className="cursor-pointer list-none font-medium text-zinc-200">
                      {question}
                      <span className="float-right text-purple-400 transition-transform group-open:rotate-45">
                        +
                      </span>
                    </summary>
                    <p className="mt-3 text-sm leading-6 text-zinc-500">
                      {answer}
                    </p>
                  </details>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
