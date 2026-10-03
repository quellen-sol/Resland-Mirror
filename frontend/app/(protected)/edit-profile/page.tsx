import type { Metadata } from "next";
import { getUserProfileData, requireOnboardedUser } from "@/lib/db";
import type { ProfileFormValues } from "@/components/profile-form";
import { rowsToGroups } from "@/lib/skills";
import HelpTip from "@/components/help-tip";
import EditProfileForm from "./edit-profile-form";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Edit Profile" };

function toDateString(date: string | null): string {
  return date ?? "";
}

export default async function EditProfilePage() {
  const user = await requireOnboardedUser();

  const { skills, experiences, bullets, education, projects, socialLinks } =
    await getUserProfileData(user.auth0_id);

  const initial: ProfileFormValues = {
    fullName: user.full_name ?? "",
    email: user.email ?? "",
    phone: user.phone ?? "",
    location: user.location ?? "",
    socialLinks: socialLinks.map((l) => ({ type: l.type, link: l.link })),
    skillGroups: rowsToGroups(
      skills.map((s) => ({ name: s.name, category: s.category })),
    ),
    experiences: experiences.map((e) => ({
      id: e.id,
      companyName: e.company_name,
      title: e.title,
      startDate: toDateString(e.start_date),
      endDate: toDateString(e.end_date),
      description: e.description ?? "",
      bullets: bullets
        .filter((b) => b.user_experience_id === e.id)
        .map((b) => ({ id: b.id, text: b.bullet })),
    })),
    education: education.map((e) => ({
      institution: e.institution,
      degree: e.degree,
      fieldOfStudy: e.field_of_study,
      startDate: toDateString(e.start_date),
      endDate: toDateString(e.end_date),
      description: e.description ?? "",
    })),
    projects: projects.map((p) => ({
      name: p.name,
      link: p.link ?? "",
      description: p.description ?? "",
      startDate: toDateString(p.start_date),
      endDate: toDateString(p.end_date),
    })),
  };

  if (initial.experiences.length === 0) {
    initial.experiences = [
      {
        companyName: "",
        title: "",
        startDate: "",
        endDate: "",
        description: "",
        bullets: [],
      },
    ];
  }

  return (
    <div className="relative flex flex-1 justify-center overflow-clip bg-zinc-950 px-6 py-10 font-sans">
      <Backdrop />

      <main className="relative w-full max-w-3xl">
        <div className="flex items-center gap-2">
          <h1 className="text-3xl font-semibold tracking-[-0.03em]">
            Edit Profile
          </h1>
          <HelpTip title="Edit Profile">
            <p>
              This is your base resume. Suggestions, tailoring and exports all
              read from it, so save your changes to keep it current.
            </p>
          </HelpTip>
        </div>
        <p className="mt-1 text-sm text-zinc-400">
          Update your contact info, links, experience, education, projects, and
          skills.
        </p>
        <div className="mt-8">
          <EditProfileForm initial={initial} />
        </div>
      </main>
    </div>
  );
}
