import type { Metadata } from "next";
import {
  Briefcase,
  ClipboardCheck,
  FileText,
  FolderGit2,
  GraduationCap,
  Link2,
  UserRound,
} from "lucide-react";
import { auth0 } from "@/lib/auth0";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUserProfileData, requireOnboardedUser } from "@/lib/db";
import { groupSkills } from "@/lib/skills";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "cn";
import CopyButton from "@/components/copy-button";
import HelpTip from "@/components/help-tip";
import JobStatusPoller from "@/components/job-status-poller";
import SuggestionDialog from "@/components/suggestion-dialog";
import DashboardMenu from "./dashboard-menu";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Dashboard" };

function fmtDate(date: string | null) {
  if (!date) return "Present";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

// social_link.type values — show the brand name, not the raw enum.
const SOCIAL_LINK_LABELS: Record<string, string> = {
  LINKEDIN: "LinkedIn",
  GITHUB: "GitHub",
  WEBSITE: "Website",
};

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-zinc-500">{text}</p>;
}

// Agent/user-entered links may lack a scheme — without one, <a href> resolves
// relative to the current page.
function normalizeHref(url: string) {
  return /^[a-z][a-z0-9+.-]*:/i.test(url) ? url : `https://${url}`;
}

export default async function DashboardPage() {
  const [session, user] = await Promise.all([
    auth0.getSession(),
    requireOnboardedUser(),
  ]);
  const accessToken = await getAccessTokenOrLogin("/dashboard");

  const {
    uploadJobs,
    skills,
    experiences,
    bullets,
    education,
    projects,
    socialLinks,
  } = await getUserProfileData(user.auth0_id);

  const activeJobIds = uploadJobs
    .filter((j) => j.status === "PENDING" || j.status === "PROCESSING")
    .map((j) => j.id);

  const bulletsFor = (expId: number) =>
    bullets.filter((b) => b.user_experience_id === expId);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />

      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <JobStatusPoller jobIds={activeJobIds} />
        <header className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-semibold tracking-[-0.03em]">
                Dashboard
              </h1>
              <HelpTip title="Your Dashboard">
                <p>
                  This is your base resume, the version everything else starts
                  from. Tailoring, suggestions and exports all use it, so keep
                  it current.
                </p>
                <p>
                  The sparkle asks for a suggestion on a bullet or a whole job.
                  The copy icon copies a bullet to your clipboard.
                </p>
              </HelpTip>
            </div>
            <p className="mt-1 truncate text-sm text-zinc-400">
              {user.full_name ?? session?.user.name ?? session?.user.email}
            </p>
          </div>
          <DashboardMenu
            accessToken={accessToken}
            isAdmin={user.site_admin}
            uploadDisabled={activeJobIds.length > 0}
          />
        </header>

        {/* Contact */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <UserRound className="size-4 text-brand-400" /> Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
              {(
                [
                  ["Name", user.full_name],
                  ["Email", user.email],
                  ["Phone", user.phone],
                  ["Location", user.location],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                    {label}
                  </p>
                  <p
                    className={cn(
                      "text-sm",
                      value ? "text-zinc-100" : "text-zinc-600",
                    )}
                  >
                    {value ?? "—"}
                  </p>
                </div>
              ))}
            </div>
            {socialLinks.length > 0 && (
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                {socialLinks.map((link) => (
                  <a
                    key={link.id}
                    href={normalizeHref(link.link)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-brand-300 underline-offset-4 hover:underline"
                  >
                    <Link2 className="size-3.5" />
                    {SOCIAL_LINK_LABELS[link.type] ?? link.type.toLowerCase()}
                  </a>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Professional summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="size-4 text-brand-400" /> Professional Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            {user.summary ? (
              <p className="text-sm whitespace-pre-wrap text-zinc-300">
                {user.summary}
              </p>
            ) : (
              <Empty text="No summary yet. Upload a resume that has one and it'll show up here." />
            )}
          </CardContent>
        </Card>

        {/* Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ClipboardCheck className="size-4 text-brand-400" /> Skills
            </CardTitle>
          </CardHeader>
          <CardContent>
            {skills.length === 0 ? (
              <Empty text="No skills added yet." />
            ) : (
              <div className="flex flex-col gap-3">
                {groupSkills(
                  skills.map((s) => ({ name: s.name, category: s.category })),
                ).map((group, gi) => (
                  <div key={group.category ?? `ungrouped-${gi}`}>
                    {group.category !== null && (
                      <p className="mb-1.5 text-xs font-medium tracking-wide text-zinc-500 uppercase">
                        {group.category}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {group.skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-md border border-brand-500/30 bg-brand-500/10 px-2 py-0.5 text-sm text-brand-200"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Work experience */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Briefcase className="size-4 text-brand-400" /> Work Experience
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {experiences.length === 0 && (
              <Empty text="No experience added yet." />
            )}
            {experiences.map((exp) => (
              <div key={exp.id} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">
                    {exp.title}
                    <span className="text-zinc-400">
                      {" "}
                      · {exp.company_name}
                      {exp.location && ` · ${exp.location}`}
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2 text-xs text-zinc-500">
                    {fmtDate(exp.start_date)} – {fmtDate(exp.end_date)}
                    <SuggestionDialog
                      accessToken={accessToken}
                      experienceId={exp.id}
                      contextLabel={`${exp.title} · ${exp.company_name}`}
                      targetText={
                        bulletsFor(exp.id)
                          .map((b) => b.bullet)
                          .join("\n") || undefined
                      }
                      // Plain fields only — the ORM row's Temporal created_at
                      // can't cross into a client component.
                      bullets={bulletsFor(exp.id).map(({ id, bullet }) => ({
                        id,
                        bullet,
                      }))}
                    />
                  </span>
                </div>
                {exp.description && (
                  <p className="text-sm text-zinc-400">{exp.description}</p>
                )}
                {bulletsFor(exp.id).length > 0 && (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-zinc-400">
                    {bulletsFor(exp.id).map((b) => (
                      <li key={b.id}>
                        {/* Actions lead the text so they sit at a fixed spot
                            no matter how long the bullet runs. */}
                        <span className="mr-1.5 inline-flex items-center gap-1 align-middle">
                          <SuggestionDialog
                            accessToken={accessToken}
                            experienceId={exp.id}
                            bulletId={b.id}
                            targetText={b.bullet}
                            contextLabel={`${exp.title} · ${exp.company_name}`}
                            variant="icon"
                          />
                          <CopyButton text={b.bullet} />
                        </span>
                        {b.bullet}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Education */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <GraduationCap className="size-4 text-brand-400" /> Education
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {education.length === 0 && <Empty text="No education added yet." />}
            {education.map((edu) => (
              <div key={edu.id} className="flex flex-col gap-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">
                    {edu.degree}
                    <span className="text-zinc-400"> · {edu.institution}</span>
                  </span>
                  <span className="shrink-0 text-xs text-zinc-500">
                    {fmtDate(edu.start_date)} – {fmtDate(edu.end_date)}
                  </span>
                </div>
                <p className="text-sm text-zinc-400">{edu.field_of_study}</p>
                {edu.description && (
                  <p className="text-sm text-zinc-500">{edu.description}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Projects */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FolderGit2 className="size-4 text-brand-400" /> Projects
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {projects.length === 0 && <Empty text="No projects added yet." />}
            {projects.map((proj) => (
              <div key={proj.id} className="flex flex-col gap-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">
                    {proj.name}
                    {proj.link && (
                      <>
                        {" "}
                        <a
                          href={normalizeHref(proj.link)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-brand-300 underline-offset-4 hover:underline"
                        >
                          link
                        </a>
                      </>
                    )}
                  </span>
                  <span className="shrink-0 text-xs text-zinc-500">
                    {fmtDate(proj.start_date)} – {fmtDate(proj.end_date)}
                  </span>
                </div>
                {proj.description && (
                  <p className="text-sm text-zinc-400">{proj.description}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

      </main>
    </div>
  );
}
