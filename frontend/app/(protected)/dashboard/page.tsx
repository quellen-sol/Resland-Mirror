import { redirect } from "next/navigation";
import Link from "next/link";
import type { Temporal } from "temporal-polyfill";
import {
  Briefcase,
  ClipboardCheck,
  FolderGit2,
  GraduationCap,
  Link2,
  PenLine,
  Upload,
} from "lucide-react";
import { auth0 } from "@/lib/auth0";
import { getUser, getUserProfileData } from "@/lib/db";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "cn";
import JobStatusPoller from "@/components/job-status-poller";
import UploadResumeDialog from "./upload-resume-dialog";

function fmtDate(date: Temporal.Instant | null) {
  if (!date) return "Present";
  return new Date(date.epochMilliseconds).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

const statusStyles: Record<string, string> = {
  PENDING: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  PROCESSING: "border-purple-500/30 bg-purple-500/10 text-purple-300",
  COMPLETED: "border-green-500/30 bg-green-500/10 text-green-300",
  FAILED: "border-red-500/30 bg-red-500/10 text-red-300",
};

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-zinc-500">{text}</p>;
}

export default async function DashboardPage() {
  const [session, user] = await Promise.all([auth0.getSession(), getUser()]);
  if (!user) redirect("/auth/login");

  const {
    uploadJobs,
    skills,
    experiences,
    bullets,
    education,
    projects,
    socialLinks,
  } = await getUserProfileData(user.auth0Id);

  const activeJobIds = uploadJobs
    .filter((j) => j.status === "PENDING" || j.status === "PROCESSING")
    .map((j) => j.id);

  const bulletsFor = (expId: number) =>
    bullets.filter((b) => b.userJobExperienceId === expId);

  return (
    <div className="relative flex flex-1 justify-center overflow-hidden bg-zinc-950 px-6 py-10 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />

      <main className="relative flex w-full max-w-3xl flex-col gap-6">
        <JobStatusPoller jobIds={activeJobIds} />
        <header className="flex items-center justify-between">
          <div>
            <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
              Dashboard
            </h1>
            <p className="mt-1 text-sm text-zinc-400">
              {user.fullName ?? session?.user.name ?? session?.user.email}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <UploadResumeDialog
              userId={user.auth0Id}
              disabled={activeJobIds.length > 0}
            />
            <Link
              href="/edit-profile"
              className={cn(
                buttonVariants({ variant: "outline", size: "sm" }),
                "border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100",
              )}
            >
              <PenLine /> Edit profile
            </Link>
            <a
              href="/auth/logout"
              className="px-1 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
            >
              Sign out
            </a>
          </div>
        </header>

        {/* Contact */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardContent className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-6">
            {user.fullName && (
              <span className="font-medium text-zinc-100">{user.fullName}</span>
            )}
            {user.email && (
              <span className="text-sm text-zinc-400">{user.email}</span>
            )}
            {user.phone && (
              <span className="text-sm text-zinc-400">{user.phone}</span>
            )}
            {user.location && (
              <span className="text-sm text-zinc-400">{user.location}</span>
            )}
            {socialLinks.map((link) => (
              <a
                key={link.id}
                href={link.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-purple-300 underline-offset-4 hover:underline"
              >
                <Link2 className="size-3.5" />
                {link.type.toLowerCase()}
              </a>
            ))}
            {!user.fullName &&
              !user.email &&
              !user.phone &&
              !user.location &&
              socialLinks.length === 0 && (
                <Empty text="No contact info yet — add it via Edit profile." />
              )}
          </CardContent>
        </Card>

        {/* Resume uploads */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Upload className="size-4 text-purple-400" /> Resume uploads
            </CardTitle>
            <CardDescription className="text-zinc-400">
              Files you&apos;ve uploaded for parsing.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {uploadJobs.length === 0 && (
              <Empty text="No uploads yet." />
            )}
            {uploadJobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2"
              >
                <span className="truncate font-mono text-xs text-zinc-400">
                  {job.id}
                </span>
                <Badge
                  variant="outline"
                  className={statusStyles[job.status] ?? ""}
                >
                  {job.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Skills */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ClipboardCheck className="size-4 text-purple-400" /> Skills
            </CardTitle>
          </CardHeader>
          <CardContent>
            {skills.length === 0 ? (
              <Empty text="No skills added yet." />
            ) : (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <span
                    key={skill.id}
                    className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-sm text-purple-200"
                  >
                    {skill.name}
                  </span>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Work experience */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Briefcase className="size-4 text-purple-400" /> Work experience
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
                    <span className="text-zinc-400"> · {exp.companyName}</span>
                  </span>
                  <span className="shrink-0 text-xs text-zinc-500">
                    {fmtDate(exp.startDate)} — {fmtDate(exp.endDate)}
                  </span>
                </div>
                {exp.description && (
                  <p className="text-sm text-zinc-400">{exp.description}</p>
                )}
                {bulletsFor(exp.id).length > 0 && (
                  <ul className="list-inside list-disc text-sm text-zinc-400">
                    {bulletsFor(exp.id).map((b) => (
                      <li key={b.id}>{b.bullet}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Education */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <GraduationCap className="size-4 text-purple-400" /> Education
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {education.length === 0 && (
              <Empty text="No education added yet." />
            )}
            {education.map((edu) => (
              <div key={edu.id} className="flex flex-col gap-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">
                    {edu.degree}
                    <span className="text-zinc-400"> · {edu.institution}</span>
                  </span>
                  <span className="shrink-0 text-xs text-zinc-500">
                    {fmtDate(edu.startDate)} — {fmtDate(edu.endDate)}
                  </span>
                </div>
                <p className="text-sm text-zinc-400">{edu.fieldOfStudy}</p>
                {edu.description && (
                  <p className="text-sm text-zinc-500">{edu.description}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Projects */}
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FolderGit2 className="size-4 text-purple-400" /> Projects
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
                          href={proj.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-purple-300 underline-offset-4 hover:underline"
                        >
                          link
                        </a>
                      </>
                    )}
                  </span>
                  <span className="shrink-0 text-xs text-zinc-500">
                    {fmtDate(proj.startDate)} — {fmtDate(proj.endDate)}
                  </span>
                </div>
                {proj.description && (
                  <p className="text-sm text-zinc-400">{proj.description}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Separator className="bg-zinc-800" />
        <p className="pb-6 text-center text-xs text-zinc-600">
          AI-powered suggestions are coming soon.
        </p>
      </main>
    </div>
  );
}
