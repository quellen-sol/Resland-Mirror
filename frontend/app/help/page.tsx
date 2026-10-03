import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import SiteFooter from "@/components/site-footer";

export const metadata: Metadata = {
  title: "Help & FAQ",
  // The root layout's canonical is "/" — override it so /help indexes as
  // its own page.
  alternates: { canonical: "/help" },
};

// This page is otherwise fully static; re-render daily so the footer's
// copyright year doesn't stay frozen at the last build.
export const revalidate = 86400;

/** "Billing & Credits" -> "faq-billing-credits" — a valid, space-free id. */
function sectionId(title: string) {
  return `faq-${title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")}`;
}

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
        "When you first sign in, you can upload an existing resume (we read it and fill in your profile automatically) or enter your information by hand. If you skipped that step, upload a resume or open Edit Profile from the dashboard menu.",
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
        "The sparkle next to a bullet or job asks the AI for a suggestion. It may ask you a question or two, then proposes a rewrite you can accept or dismiss. You can also tell it what you'd like changed in your own words.",
      ],
      [
        "How do I tailor my resume to a job?",
        "Open Tailor Resume from the dashboard menu and paste the job description. The AI rewrites and reorders your bullets to match it. Results aren't saved automatically — click Save to Tailored Resumes to keep one, then edit and export it from your Tailored Resumes board.",
      ],
      [
        "Can I copy a bullet point?",
        "Yes — the copy icon next to each bullet on the dashboard copies its text to your clipboard.",
      ],
      [
        "Which AI model is used?",
        "You can pick a model when you ask for a suggestion or tailor a resume, or just use the default. More capable models usually cost more each time you use them.",
      ],
    ],
  },
  {
    title: "System Design Practice",
    faqs: [
      [
        "What is the System Design Mock?",
        "A practice system design interview with an AI interviewer. Pick a problem from the practice bank, or one written from a job you tailored your resume for. You clarify requirements, estimate the scale, draw your design, then answer deep-dive questions about it.",
      ],
      [
        "How do I draw my design?",
        "Add components from the palette above the whiteboard and connect them with the arrow tool. Drag each end of an arrow onto a box until it snaps — the interviewer reads which boxes your arrows connect, so loose arrows and plain lines don't count. Submitting your design points out anything that isn't connected.",
      ],
      [
        "How am I graded?",
        "You're scored from 1 to 5 against the level you chose on requirements, estimation, high-level design, the deep dive, communication, and time management. The weighted score becomes a letter grade and a hire signal, and the report shows a reference design to compare against.",
      ],
      [
        "What does an interview cost?",
        "Each interviewer reply and the final grading draw from your balance, like tailoring does. Starting a practice-bank problem is free; a problem written from a job posting costs one AI call to prepare.",
      ],
    ],
  },
  {
    title: "Billing & Credits",
    faqs: [
      [
        "How does billing work?",
        "Resland is pay-as-you-go — no subscription. You buy balance in packs on the Billing page, and AI features (suggestions and tailoring) draw from it. Bigger packs include bonus balance.",
      ],
      [
        "How much does each action cost?",
        "You're charged for what each request actually uses: the AI provider's cost for that work, plus a service fee. Longer resumes and job descriptions take more work, and more capable models cost more. Any prices shown next to a model are estimates — your actual charge is based on what was really used.",
      ],
      [
        "What if my balance runs out partway through?",
        "Anything that's already started is never interrupted — the charge is taken afterward and simply can't take your balance below zero. You just need a balance above zero to start something new.",
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
        "Resumes export as editable Word (.docx) documents so you can make final tweaks before sending them out.",
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
            preload
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
            <section
              key={section.title}
              aria-labelledby={sectionId(section.title)}
            >
              <h2
                id={sectionId(section.title)}
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
