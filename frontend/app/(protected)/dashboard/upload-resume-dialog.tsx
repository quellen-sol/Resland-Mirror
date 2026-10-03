"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "cn";
import UploadForm from "@/components/upload-form";

export default function UploadResumeDialog({
  accessToken,
  disabled,
}: {
  accessToken: string;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        disabled={disabled}
        title={
          disabled
            ? "Your current resume is still being processed"
            : undefined
        }
        className={cn(
          buttonVariants({ size: "sm" }),
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <Upload /> Upload New Resume
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-zinc-100">
            Upload a New Resume
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            We&apos;ll read your resume and update your profile.
          </DialogDescription>
        </DialogHeader>
        <UploadForm
          accessToken={accessToken}
          onSuccess={() => {
            setOpen(false);
            router.refresh();
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
