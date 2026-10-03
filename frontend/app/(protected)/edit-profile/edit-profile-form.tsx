"use client";

import { useState, useTransition } from "react";
import { CircleAlert } from "lucide-react";
import ProfileForm, {
  ProfileFormValues,
} from "@/components/profile-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toProfileInput } from "@/lib/profile-input";
import { saveProfileEdit } from "./actions";

export default function EditProfileForm({
  initial,
}: {
  initial: ProfileFormValues;
}) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(values: ProfileFormValues) {
    setError(null);
    startTransition(async () => {
      try {
        await saveProfileEdit(toProfileInput(values));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    });
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <Alert
          variant="destructive"
          className="border-red-500/30 bg-red-500/10"
        >
          <CircleAlert />
          <AlertTitle>Couldn&apos;t save</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <ProfileForm
        initial={initial}
        pending={isPending}
        submitLabel="Save Changes"
        cancelHref="/dashboard"
        onSubmit={handleSubmit}
      />
    </div>
  );
}
