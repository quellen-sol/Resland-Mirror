import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUser } from "@/lib/db";
import { getSiteSettings } from "@/lib/settings";
import BillingClient from "./billing-client";

export const metadata: Metadata = { title: "Billing" };

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{ checkout?: string }>;
}) {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  const accessToken = await getAccessTokenOrLogin("/billing");
  const [{ checkout }, settings] = await Promise.all([
    searchParams,
    getSiteSettings(),
  ]);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <BillingClient
          accessToken={accessToken}
          checkoutResult={checkout ?? null}
          paymentsPaused={settings.payments_paused}
        />
      </main>
    </div>
  );
}
