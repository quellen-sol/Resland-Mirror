import Image from "next/image";
import Link from "next/link";
import { FileText, Gauge, MessageCircleQuestion, Sparkles } from "lucide-react";
import { redirect } from "next/navigation";
import { auth0 } from "@/lib/auth0";
import { getUser } from "@/lib/db";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "cn";

const steps = [
  ["1", "Upload your resume", "Parsed into a structured profile."],
  ["2", "Sharpen every bullet", "AI suggestions that ask you questions first."],
  ["3", "Tailor to any job", "Paste a JD, get a reordered and rewritten resume."],
];
const features = [
  ["AI-powered suggestions", "Turn vague experience into clear, specific impact."],
  ["Tailor to every role", "Match your resume to the language hiring teams use."],
  ["One structured profile", "Keep your experience, skills, and projects in one place."],
  ["Bring your own model", "Choose the model that fits your workflow."],
  ["Pay-as-you-go credits", "Pay only for what you use — no subscription."],
  ["Your data stays yours", "Your resume is yours, and your profile stays private."],
];
const faqs = [
  ["Is Resland a subscription?", "No. Resland uses pay-as-you-go credits, so you only pay for the AI work you choose to run."],
  ["Can I use my own AI model?", "Yes. Choose from the available models when generating suggestions or tailoring a resume."],
  ["Will Resland rewrite my resume automatically?", "Resland suggests changes and asks questions first. You stay in control of what gets accepted."],
  ["What happens to my resume data?", "Your profile is stored securely for your account and is not used as someone else’s resume."],
];

export default async function Home() {
  let session: Awaited<ReturnType<typeof auth0.getSession>> = null;
  let lookupFailed = false;
  try {
    session = await auth0.getSession();
    if (session) {
      const user = await getUser();
      if (user) redirect(user.has_onboarded ? "/dashboard" : "/onboarding");
    }
  } catch {
    lookupFailed = true;
  }
  const primaryHref = lookupFailed || session ? "/dashboard" : "/auth/login?screen_hint=signup";
  const primaryLabel = lookupFailed || session ? "Go to dashboard" : "Get started";
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
    <div className="relative flex flex-1 flex-col overflow-hidden bg-zinc-950 font-sans text-zinc-100">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[600px] bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <Image src="/resland-logo.png" alt="Resland" width={32} height={32} priority className="rounded-lg" /> Resland
        </Link>
        <Link href="/auth/login?returnTo=/dashboard" className={cn(buttonVariants({ variant: "ghost" }), "text-zinc-300")}>Log in</Link>
      </header>
      <main className="relative mx-auto flex w-full min-w-0 max-w-6xl flex-1 flex-col gap-24 overflow-hidden px-6 pb-20 pt-16 sm:px-8 sm:pt-24">
        <section className="flex w-full min-w-0 flex-col items-center text-center">
          <span className="mb-5 rounded-full border border-purple-500/20 bg-purple-500/10 px-3 py-1 text-xs text-purple-300">Resume clarity, without the busywork</span>
          <h1 className="w-full max-w-[calc(100vw-3rem)] break-words bg-gradient-to-r from-purple-300 via-violet-400 to-purple-500 bg-clip-text text-4xl leading-tight font-semibold tracking-tight text-transparent sm:max-w-3xl sm:text-7xl">Land your next role</h1>
          <p className="mt-6 w-full max-w-[calc(100vw-3rem)] break-words text-lg leading-8 text-zinc-400 sm:max-w-2xl">Upload your resume, sharpen every bullet with AI, and tailor your story to any job description in minutes.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href={primaryHref} className={cn(buttonVariants({ size: "lg" }), "h-11 border-0 bg-gradient-to-r from-violet-600 to-purple-600 px-8 text-white shadow-lg shadow-purple-950/50 hover:from-violet-500 hover:to-purple-500")}>{primaryLabel}</Link>
            <Link href="/auth/login?returnTo=/dashboard" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "h-11 border-zinc-700 bg-transparent px-8 text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100")}>Log in</Link>
          </div>
          <p className="mt-5 text-xs text-zinc-500">Pay only for what you use — no subscription</p>
        </section>
        <section aria-labelledby="how-it-works" className="w-full min-w-0">
          <h2 id="how-it-works" className="w-full max-w-[calc(100vw-3rem)] break-words text-center text-2xl font-semibold">How it works</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">{steps.map(([number, title, description]) => <div key={number} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6"><span className="text-sm font-semibold text-purple-400">{number}</span><h3 className="mt-3 font-medium">{title}</h3><p className="mt-2 text-sm leading-6 text-zinc-500">{description}</p></div>)}</div>
        </section>
        <section aria-labelledby="features" className="w-full min-w-0">
          <h2 id="features" className="w-full max-w-[calc(100vw-3rem)] break-words text-center text-2xl font-semibold">Everything you need to apply with confidence</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{features.map(([title, description], index) => { const Icon = [FileText, Sparkles, Gauge, MessageCircleQuestion, Sparkles, FileText][index]; return <div key={title} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5"><Icon className="size-5 text-purple-400" /><h3 className="mt-3 text-sm font-medium">{title}</h3><p className="mt-1 text-sm leading-6 text-zinc-500">{description}</p></div>; })}</div>
        </section>
        <section aria-labelledby="faq" className="mx-auto w-full max-w-3xl">
          <h2 id="faq" className="w-full max-w-[calc(100vw-3rem)] break-words text-center text-2xl font-semibold">Frequently asked questions</h2>
          <div className="mt-8 divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/60 px-5">{faqs.map(([question, answer]) => <details key={question} className="group py-4"><summary className="cursor-pointer list-none font-medium text-zinc-200">{question}<span className="float-right text-purple-400 transition-transform group-open:rotate-45">+</span></summary><p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-500">{answer}</p></details>)}</div>
        </section>
      </main>
      <footer className="relative border-t border-zinc-800/80 px-6 py-8 sm:px-8"><div className="mx-auto flex w-full max-w-6xl flex-col gap-4 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-2"><Image src="/resland-logo.png" alt="" width={24} height={24} className="rounded-md" /> © {new Date().getFullYear()} Resland · resland.org</div><nav className="flex gap-4"><Link href="/auth/login" className="hover:text-zinc-200">Log in</Link><Link href="/auth/login?screen_hint=signup" className="hover:text-zinc-200">Sign up</Link></nav></div></footer>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    </div>
  );
}
