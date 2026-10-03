import { getUser } from "@/lib/db";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { redirect } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import UploadForm from "@/components/upload-form";
import Backdrop from "@/components/backdrop";

export default async function TestUploadPage() {
  const user = await getUser();

  if (!user) {
    redirect("/auth/login");
  }
  const accessToken = await getAccessTokenOrLogin("/test-upload");

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-hidden bg-zinc-950 p-6 font-sans">
      <Backdrop />

      <Card className="relative w-full max-w-xl shadow-2xl shadow-brand-950/40 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-2xl tracking-[-0.03em]">
            Test Upload
          </CardTitle>
          <CardDescription className="text-zinc-400">
            Sends a file to{" "}
            <code className="rounded bg-zinc-800 px-1 py-0.5 font-mono text-[0.85em] text-brand-300">
              {"${NEXT_PUBLIC_API_BASE_URL}/upload-initial-resume"}
            </code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadForm accessToken={accessToken} />
        </CardContent>
      </Card>
    </div>
  );
}
