import { redirect } from "next/navigation";
import { FileText, Sparkles, LayoutDashboard } from "lucide-react";
import { auth0 } from "@/lib/auth0";
import { getUser } from "@/lib/db";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "cn";

const features = [
  {
    icon: FileText,
    title: "Upload your resume",
    description: "Drop in your resume and we'll parse it into structured data.",
  },
  {
    icon: Sparkles,
    title: "AI-powered improvements",
    description: "Get suggestions to sharpen your experience and skills.",
  },
  {
    icon: LayoutDashboard,
    title: "One dashboard",
    description: "See your profile, job experiences, and skills in one place.",
  },
];

export default async function Home() {
  const session = await auth0.getSession();

  if (session) {
    const user = await getUser();
    if (user) {
      redirect(user.hasOnboarded ? "/dashboard" : "/onboarding");
    }
  }

  return (
    <div className="relative flex flex-1 flex-col overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[500px] bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />

      <header className="relative flex items-center justify-between px-8 py-5">
        <span className="text-lg font-semibold tracking-tight text-zinc-100">
          Resland
        </span>
        <a
          href="/auth/login"
          className={cn(buttonVariants({ variant: "ghost" }), "text-zinc-300")}
        >
          Log in
        </a>
      </header>

      <main className="relative flex flex-1 flex-col items-center justify-center gap-10 px-6 pb-24 text-center">
        <div className="flex flex-col items-center gap-5">
          <h1 className="max-w-2xl bg-gradient-to-r from-purple-300 via-violet-400 to-purple-500 bg-clip-text text-5xl font-semibold tracking-tight text-transparent sm:text-6xl">
            Land your next role
          </h1>
          <p className="max-w-md text-lg text-zinc-400">
            Upload your resume or enter your experience — Resland turns it into
            a profile that works for you.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <a
            href="/auth/login?screen_hint=signup"
            className={cn(
              buttonVariants({ size: "lg" }),
              "h-11 border-0 bg-gradient-to-r from-violet-600 to-purple-600 px-8 text-white shadow-lg shadow-purple-950/50 hover:from-violet-500 hover:to-purple-500",
            )}
          >
            Get started
          </a>
          <a
            href="/auth/login"
            className={cn(
              buttonVariants({ variant: "outline", size: "lg" }),
              "h-11 border-zinc-700 bg-transparent px-8 text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100",
            )}
          >
            Log in
          </a>
        </div>

        <div className="mt-8 grid w-full max-w-3xl gap-4 sm:grid-cols-3">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 text-left backdrop-blur"
            >
              <Icon className="size-5 text-purple-400" />
              <h2 className="mt-3 text-sm font-medium text-zinc-100">
                {title}
              </h2>
              <p className="mt-1 text-sm text-zinc-500">{description}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
