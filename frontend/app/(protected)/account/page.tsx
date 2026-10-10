import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import Backdrop from "@/components/backdrop";
import AccountClient from "./account-client";

export const metadata: Metadata = { title: "Account & Data" };

// No onboarding gate: someone who never finished setting up can still
// download or delete what Resland holds about them.
export default async function AccountPage() {
  const accessToken = await getAccessTokenOrLogin("/account");

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
      <main className="relative mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <AccountClient accessToken={accessToken} />
      </main>
    </div>
  );
}
