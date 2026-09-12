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

export default function UploadResumeDialog({ userId }: { userId: number }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        className={cn(
          buttonVariants({ size: "sm" }),
          "border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-purple-950/50 hover:from-violet-500 hover:to-purple-500",
        )}
      >
        <Upload /> Upload New Resume
      </DialogTrigger>
      <DialogContent className="border-zinc-800 bg-zinc-900 text-zinc-100">
        <DialogHeader>
          <DialogTitle className="text-zinc-100">
            Upload a new resume
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            The file will be parsed and your profile updated.
          </DialogDescription>
        </DialogHeader>
        <UploadForm
          userId={userId}
          onSuccess={() => {
            setOpen(false);
            router.refresh();
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
