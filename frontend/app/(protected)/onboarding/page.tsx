import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import { auth0 } from "@/lib/auth0";
import OnboardingFlow from "./onboarding-flow";

export default async function OnboardingPage() {
  const user = await getUser();

  if (!user) {
    redirect("/auth/login");
  }
  if (user.hasOnboarded) {
    redirect("/dashboard");
  }
  const { token: accessToken } = await auth0.getAccessToken();

  return <OnboardingFlow accessToken={accessToken} />;
}
