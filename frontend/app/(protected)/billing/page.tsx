import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { requireOnboardedUser } from "@/lib/db";
import { getSiteSettings } from "@/lib/settings";
import BillingClient from "./billing-client";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Billing" };

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{ checkout?: string }>;
}) {
  await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin("/billing");
  const [{ checkout }, settings] = await Promise.all([
    searchParams,
    getSiteSettings(),
  ]);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
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
