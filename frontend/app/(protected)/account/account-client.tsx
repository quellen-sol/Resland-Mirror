"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2, Trash2, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  apiDownload,
  apiFetch,
  describeApiError,
  fmtCents,
} from "@/lib/api";
import {
  DELETE_CONFIRMATION,
  apiErrorDetail,
  exportFilename,
  isDeleteConfirmed,
} from "@/lib/account";

// Deletion talks to Stripe, S3 and Auth0 in turn — give it longer than the
// default request timeout.
const DELETE_TIMEOUT_MS = 60_000;

// describeApiError reads every 502-504 as "can't reach the servers", but
// these endpoints answer 502/503 with an explanation in `detail` (Stripe or
// Auth0 refused, deletion not configured yet). A load balancer's error page
// has no such detail and still gets the generic message.
function errorMessage(error: unknown) {
  if (error instanceof ApiError && error.status >= 502 && error.status <= 504) {
    const detail = apiErrorDetail(error.message);
    if (detail) return detail;
  }
  return describeApiError(error);
}

export default function AccountClient({ accessToken }: { accessToken: string }) {
  const confirmId = useId();
  const [balance, setBalance] = useState<number | null>(null);
  const [exporting, setExporting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  function loadBalance() {
    apiFetch(accessToken, "/billing/balance")
      .then((res) => setBalance((res as { balance_cents: number }).balance_cents))
      // Unknown balance: the warning falls back to "any balance left".
      .catch(() => setBalance(null));
  }

  useEffect(() => {
    loadBalance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  async function downloadData() {
    setExporting(true);
    try {
      await apiDownload(accessToken, "/account/export", exportFilename(new Date()));
      toast.success("Your data is downloading");
    } catch (e) {
      toast.error("Couldn't export your data", { description: errorMessage(e) });
    } finally {
      setExporting(false);
    }
  }

  function openConfirm() {
    setTyped("");
    setDeleteError(null);
    setConfirmOpen(true);
    // Re-read so the warning shows what will actually be lost.
    loadBalance();
  }

  async function deleteAccount() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiFetch(accessToken, "/account", {
        method: "DELETE",
        signal: AbortSignal.timeout(DELETE_TIMEOUT_MS),
      });
      // The account and its sign-in are gone; signing out clears the
      // session cookie this browser still holds. /auth/logout is the Auth0
      // SDK's route, not a page, so it needs a full navigation (like the
      // menu's Sign Out link), not the client router.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/auth/logout");
    } catch (e) {
      setDeleteError(errorMessage(e));
      setDeleting(false);
      // A payment the webhook missed may just have been credited (409), so
      // the warning must show the balance that would now be forfeited.
      loadBalance();
    }
  }

  const balanceWarning =
    balance === null ? (
      <>Any balance left on your account will be lost.</>
    ) : (
      <>
        Your balance of{" "}
        <span className="font-semibold text-amber-100">{fmtCents(balance)}</span>{" "}
        will be lost.
      </>
    );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-[-0.03em]">
            Account &amp; Data
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Download a copy of your data, or delete your account.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Download className="size-4 text-brand-400" /> Download Your Data
          </CardTitle>
          <CardDescription className="text-zinc-400">
            A .zip with everything Resland stores about you: your profile,
            memory, tailored resumes, suggestions, mock interview transcripts
            and reports, purchases and charges, and the files you uploaded or
            exported. A README inside explains each part.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={downloadData} disabled={exporting}>
            {exporting ? <Loader2 className="animate-spin" /> : <Download />}
            Download My Data
          </Button>
        </CardContent>
      </Card>

      <Card className="ring-red-900/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg text-red-300">
            <Trash2 className="size-4" /> Delete Your Account
          </CardTitle>
          <CardDescription className="text-zinc-400">
            Permanently deletes your profile, memory, uploaded and generated
            resumes, tailored resumes, suggestions, mock interviews and study
            progress, and removes your sign-in. Records of your purchases and
            charges are kept for our accounting, no longer linked to you. This
            can&apos;t be undone.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="flex items-start gap-2 rounded-lg bg-amber-950/40 px-3 py-2 text-sm text-amber-200 ring-1 ring-amber-800/60">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            <span>
              {balanceWarning} Unused balance isn&apos;t refunded when you
              delete your account.
            </span>
          </p>
          <div>
            <Button variant="destructive" onClick={openConfirm}>
              <Trash2 /> Delete Account…
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={confirmOpen}
        onOpenChange={(open) => {
          if (!deleting) setConfirmOpen(open);
        }}
      >
        <DialogContent showCloseButton={!deleting}>
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Delete your account?
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Everything in your Resland account is deleted for good, and you
              won&apos;t be able to sign in to it again. Want a copy first?
              Download your data before you continue.
            </DialogDescription>
          </DialogHeader>
          <p className="rounded-lg bg-amber-950/40 px-3 py-2 text-sm text-amber-200 ring-1 ring-amber-800/60">
            {balanceWarning} It isn&apos;t refunded.
          </p>
          <div className="flex flex-col gap-2">
            <Label htmlFor={confirmId} className="text-zinc-300">
              Type {DELETE_CONFIRMATION} to confirm
            </Label>
            <Input
              id={confirmId}
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
              spellCheck={false}
              disabled={deleting}
              placeholder={DELETE_CONFIRMATION}
            />
          </div>
          {deleteError && (
            <p role="alert" className="text-sm text-red-300">
              {deleteError}
            </p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={deleting}
              className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={deleteAccount}
              disabled={!isDeleteConfirmed(typed) || deleting}
            >
              {deleting ? <Loader2 className="animate-spin" /> : <Trash2 />}
              Delete My Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
