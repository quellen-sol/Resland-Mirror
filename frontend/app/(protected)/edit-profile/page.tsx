import { redirect } from "next/navigation";
import type { Temporal } from "temporal-polyfill";
import { getUser, getUserProfileData } from "@/lib/db";
import type { ProfileFormValues } from "@/components/profile-form";
import EditProfileForm from "./edit-profile-form";

function toDateString(date: Temporal.Instant | null): string {
  return date ? date.toString().slice(0, 10) : "";
}

export default async function EditProfilePage() {
  const user = await getUser();
  if (!user) redirect("/auth/login");

  const { skills, experiences, bullets, education, projects, socialLinks } =
    await getUserProfileData(user.id);

  const initial: ProfileFormValues = {
    fullName: user.fullName ?? "",
    email: user.email ?? "",
    phone: user.phone ?? "",
    location: user.location ?? "",
    socialLinks: socialLinks.map((l) => ({ type: l.type, link: l.link })),
    skills: skills.map((s) => s.name),
    experiences: experiences.map((e) => ({
      companyName: e.companyName,
      title: e.title,
      startDate: toDateString(e.startDate),
      endDate: toDateString(e.endDate),
      description: e.description ?? "",
      bulletsText: bullets
        .filter((b) => b.userJobExperienceId === e.id)
        .map((b) => b.bullet)
        .join("\n"),
    })),
    education: education.map((e) => ({
      institution: e.institution,
      degree: e.degree,
      fieldOfStudy: e.fieldOfStudy,
      startDate: toDateString(e.startDate),
      endDate: toDateString(e.endDate),
      description: e.description ?? "",
    })),
    projects: projects.map((p) => ({
      name: p.name,
      link: p.link ?? "",
      description: p.description ?? "",
      startDate: toDateString(p.startDate),
      endDate: toDateString(p.endDate),
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
        bulletsText: "",
      },
    ];
  }

  return (
    <div className="relative flex flex-1 justify-center overflow-hidden bg-zinc-950 px-6 py-10 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />

      <main className="relative w-full max-w-3xl">
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
          Edit profile
        </h1>
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
