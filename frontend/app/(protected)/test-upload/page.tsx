import { getUser } from "@/lib/db";
import UploadForm from "./upload-form";

export default async function TestUploadPage() {
  const user = await getUser();

  if (!user) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-950 p-6 font-sans">
        <p className="text-zinc-400">Could not resolve your user account.</p>
      </div>
    );
  }

  return <UploadForm userId={user.id} />;
}
