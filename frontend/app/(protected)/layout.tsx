import { requireUser } from "@/lib/auth";
import { Toaster } from "@/components/ui/sonner";
import type { Metadata } from "next";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await requireUser();
  return (
    <>
      {children}
      <Toaster theme="dark" richColors position="bottom-right" />
    </>
  );
}
