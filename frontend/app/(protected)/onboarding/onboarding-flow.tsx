"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CircleAlert, FileText, PenLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import UploadForm from "@/components/upload-form";
import ProfileForm, { ProfileFormValues } from "@/components/profile-form";
import { toProfileInput } from "@/lib/profile-input";
import { completeOnboarding, saveManualProfile } from "./actions";

type Step = "choice" | "upload" | "manual";

export default function OnboardingFlow({ userId }: { userId: number }) {
  const router = useRouter();
  const [step, setStep] = useState<Step>("choice");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleSkip() {
    startTransition(async () => {
      await completeOnboarding();
      router.push("/dashboard");
    });
  }

  function handleUploadSuccess() {
    startTransition(async () => {
      await completeOnboarding();
      router.push("/dashboard");
    });
  }

  function handleSaveManual(values: ProfileFormValues) {
    setError(null);
    startTransition(async () => {
      try {
        await saveManualProfile(toProfileInput(values));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    });
  }

  return (
    <div className="relative flex flex-1 justify-center overflow-hidden bg-zinc-950 px-6 py-10 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />

      <div className="relative w-full max-w-3xl">
        {step === "choice" && (
          <div className="flex flex-col items-center gap-8">
            <div className="text-center">
              <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
                Welcome to Resland
              </h1>
              <p className="mt-2 text-zinc-400">
                How would you like to build your profile?
              </p>
            </div>

            <div className="grid w-full gap-4 sm:grid-cols-2">
              <button
                onClick={() => setStep("upload")}
                className="group rounded-xl border border-zinc-800 bg-zinc-900/80 p-6 text-left transition-colors hover:border-purple-500/50 hover:bg-zinc-900"
              >
                <FileText className="size-6 text-purple-400" />
                <h2 className="mt-4 text-lg font-medium text-zinc-100">
                  Upload a resume
                </h2>
                <p className="mt-1 text-sm text-zinc-500">
                  We&apos;ll parse your resume and fill in your profile for you.
                </p>
              </button>

              <button
                onClick={() => setStep("manual")}
                className="group rounded-xl border border-zinc-800 bg-zinc-900/80 p-6 text-left transition-colors hover:border-purple-500/50 hover:bg-zinc-900"
              >
                <PenLine className="size-6 text-purple-400" />
                <h2 className="mt-4 text-lg font-medium text-zinc-100">
                  Enter my own information
                </h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Add your experience, education, projects, and skills manually.
                </p>
              </button>
            </div>

            <button
              onClick={handleSkip}
              disabled={isPending}
              className="text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline disabled:opacity-50"
            >
              Skip for now
            </button>
          </div>
        )}

        {step === "upload" && (
          <Card className="mx-auto w-full max-w-xl border-zinc-800 bg-zinc-900/80 text-zinc-100">
            <CardHeader>
              <CardTitle className="text-xl">Upload your resume</CardTitle>
              <CardDescription className="text-zinc-400">
                PDF, DOCX, or whatever you&apos;ve got.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <UploadForm userId={userId} onSuccess={handleUploadSuccess} />
              <Button
                variant="ghost"
                onClick={() => setStep("choice")}
                className="self-start text-zinc-400 hover:text-zinc-200"
              >
                <ArrowLeft /> Back
              </Button>
            </CardContent>
          </Card>
        )}

        {step === "manual" && (
          <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
            <CardHeader>
              <CardTitle className="text-xl">Your information</CardTitle>
              <CardDescription className="text-zinc-400">
                Fill in as much as you&apos;d like — you can always edit later.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              {error && (
                <Alert
                  variant="destructive"
                  className="border-red-500/30 bg-red-500/10"
                >
                  <CircleAlert />
                  <AlertTitle>Couldn&apos;t save</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <ProfileForm
                pending={isPending}
                submitLabel="Save and continue"
                onSubmit={handleSaveManual}
              />

              <Button
                variant="ghost"
                onClick={() => setStep("choice")}
                className="self-start text-zinc-400 hover:text-zinc-200"
              >
                <ArrowLeft /> Back
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
