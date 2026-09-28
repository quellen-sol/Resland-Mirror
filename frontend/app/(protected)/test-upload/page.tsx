import { requireOnboardedUser } from "@/lib/db";
import { getAccessTokenOrLogin } from "@/lib/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import UploadForm from "@/components/upload-form";

export default async function TestUploadPage() {
  await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin("/test-upload");

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-hidden bg-zinc-950 p-6 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />

      <Card className="relative w-full max-w-xl border-zinc-800 bg-zinc-900/80 text-zinc-100 shadow-2xl shadow-purple-950/40 backdrop-blur">
        <CardHeader>
          <CardTitle className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-2xl text-transparent">
            Test Upload
          </CardTitle>
          <CardDescription className="text-zinc-400">
            Sends a file to{" "}
            <code className="rounded bg-zinc-800 px-1 py-0.5 font-mono text-[0.85em] text-purple-300">
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
