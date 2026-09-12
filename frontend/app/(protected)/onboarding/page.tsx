import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import OnboardingFlow from "./onboarding-flow";

export default async function OnboardingPage() {
  const user = await getUser();

  if (!user) {
    redirect("/auth/login");
  }
  if (user.hasOnboarded) {
    redirect("/dashboard");
  }

  return <OnboardingFlow userId={user.auth0Id} />;
}
