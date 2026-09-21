import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getUser } from "@/lib/db";
import { getAccessTokenOrLogin } from "@/lib/auth";
import OnboardingFlow from "./onboarding-flow";

export const metadata: Metadata = { title: "Onboarding" };

export default async function OnboardingPage() {
  const user = await getUser();

  if (!user) {
    redirect("/auth/login");
  }
  if (user.has_onboarded) {
    redirect("/dashboard");
  }
  const accessToken = await getAccessTokenOrLogin("/onboarding");

  return <OnboardingFlow accessToken={accessToken} />;
}
