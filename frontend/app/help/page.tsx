import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import SiteFooter from "@/components/site-footer";
import Backdrop from "@/components/backdrop";

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
        "Resland keeps your resume as an editable profile: your jobs, bullets, skills, education and projects. From there it helps you sharpen individual bullets, tailors the whole thing to specific job postings, and exports it as a Word file.",
      ],
      [
        "How do I set up my profile?",
        "When you first sign in, you can upload a resume (a PDF or .docx) and Resland fills in your profile from it, or you can enter everything by hand. If you skipped that step, upload a resume or open Edit Profile from the dashboard menu.",
      ],
      [
        "What is the dashboard?",
        "It's your base resume, the version everything else starts from. Tailoring, suggestions and exports all use it, so keep it current.",
      ],
    ],
  },
  {
    title: "Suggestions & Tailoring",
    faqs: [
      [
        "What does the sparkle icon do?",
        "The sparkle next to a bullet or a job asks Resland for a suggestion. It first asks a few questions about the work, like the scale, the result, or who used it, then writes three options for each bullet. Pick one and accept it, or use More Options to get three new ones, with or without saying what to change.",
      ],
      [
        "How do I tailor my resume to a job?",
        "Open Tailor Resume from the dashboard menu and paste the job description. Resland asks a few questions about the experience that matters most for the role, then reorders and rewrites your bullets to fit it. Results aren't saved on their own, so click Save to Tailored Resumes to keep one. You can edit and export it later from your Tailored Resumes board.",
      ],
      [
        "Can I copy a bullet point?",
        "Yes. The copy icon next to each bullet on the dashboard copies its text to your clipboard.",
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
        "Add components from the palette above the whiteboard and connect them with the arrow tool. Drag each end of an arrow onto a box until it snaps. The interviewer reads which boxes your arrows connect, so loose arrows and plain lines don't count. Submitting your design points out anything that isn't connected.",
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
    title: "DSA Study Center",
    faqs: [
      [
        "What is the DSA Study Center?",
        "A free guide to data structures and algorithms. Each topic explains how the idea works, how to spot it in an interview question, and walks through classic problems with code in TypeScript, Python, Go, C# and Java. You don't need an account to read it.",
      ],
      [
        "How do I track what I've studied?",
        "Sign in and use Mark as Studied at the top or bottom of a topic. Your progress is saved to your account, so it follows you to other devices, and the study center's home page shows how far along you are.",
      ],
      [
        "Can I change the code language?",
        "Yes. Pick a language on any code sample or on the study center's home page. Every sample switches with it, and your browser remembers the choice.",
      ],
    ],
  },
  {
    title: "Billing & Credits",
    faqs: [
      [
        "How does billing work?",
        "There's no subscription. You buy balance in packs on the Billing page, and suggestions and tailoring draw from it. Bigger packs include bonus balance.",
      ],
      [
        "How much does each action cost?",
        "You're charged for what each request actually uses: the AI provider's cost for that work, plus a service fee. Longer resumes and job descriptions take more work, and more capable models cost more. Prices shown next to a model are estimates. Your actual charge is based on what was really used.",
      ],
      [
        "What if my balance runs out partway through?",
        "Nothing gets cut off. The charge is taken after the work finishes, and your balance stops at zero instead of going negative. You just need a balance above zero to start something new.",
      ],
      [
        "How do purchases work?",
        "Checkout runs through Stripe, so Resland never sees your card details. Your balance usually updates a few seconds after you pay, and every purchase shows up in your purchase history.",
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
        "Your profile is private to your account. When you run a suggestion or tailor a resume, the text involved is sent to the AI model you picked so it can do the work.",
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
      <Backdrop />
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
        <h1 className="text-3xl font-semibold tracking-[-0.03em]">
          Help &amp; FAQ
        </h1>
        <p className="mt-2 text-sm text-zinc-400">
          Answers about your profile, suggestions, tailoring and billing.
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
              <div className="edge mt-4 divide-y divide-white/[.08] rounded-xl border border-white/[.08] bg-card px-5">
                {section.faqs.map(([question, answer]) => (
                  <details key={question} className="group py-4">
                    <summary className="cursor-pointer list-none font-medium text-zinc-200">
                      {question}
                      <span className="float-right text-brand-400 transition-transform group-open:rotate-45">
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
