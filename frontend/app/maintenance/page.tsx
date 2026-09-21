import type { Metadata } from "next";
import Image from "next/image";

export const metadata: Metadata = {
  title: "Down for maintenance",
  robots: { index: false, follow: false },
};

export default function MaintenancePage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-zinc-950 px-6 py-24 text-center">
      <div className="flex max-w-md flex-col items-center gap-5">
        <Image
          src="/resland-logo.png"
          alt="Resland"
          width={64}
          height={64}
          priority
        />
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
          Down for maintenance
        </h1>
        <p className="text-zinc-400">
          Resland is temporarily paused while we make some updates. Your data is
          safe — please check back shortly.
        </p>
      </div>
    </main>
  );
}
