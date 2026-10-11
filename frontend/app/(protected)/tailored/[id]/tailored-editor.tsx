"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Loader2,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch, describeApiError } from "@/lib/api";
import type {
  ExportTailoredResponse,
  TailoredContent,
} from "@/lib/tailored";

function fmtDate(date: string | null) {
  if (!date) return "Present";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

const inputClass =
  "border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30";

export default function TailoredEditor({
  accessToken,
  id,
  initialCompany,
  initialRole,
  jobDescription,
  initialContent,
  contentReadable,
}: {
  accessToken: string;
  id: string;
  initialCompany: string;
  initialRole: string;
  jobDescription: string;
  initialContent: TailoredContent;
  contentReadable: boolean;
}) {
  const router = useRouter();
  const [company, setCompany] = useState(initialCompany);
  const [role, setRole] = useState(initialRole);
  const [content, setContent] = useState<TailoredContent>(initialContent);
  const [busy, setBusy] = useState<"save" | "export" | "delete" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [newSkill, setNewSkill] = useState<Record<number, string>>({});
  const [dirty, setDirty] = useState(false);

  function mutateContent(fn: (c: TailoredContent) => TailoredContent) {
    setDirty(true);
    setContent(fn);
  }

  function setLocation(expIdx: number, location: string) {
    mutateContent((c) => ({
      ...c,
      experiences: c.experiences.map((e, i) =>
        i === expIdx
          ? { ...e, location: location.trim() ? location : null }
          : e,
      ),
    }));
  }

  function setBullet(expIdx: number, bulletIdx: number, text: string) {
    mutateContent((c) => ({
      ...c,
      experiences: c.experiences.map((e, i) =>
        i === expIdx
          ? {
              ...e,
              bullets: e.bullets.map((b, j) => (j === bulletIdx ? text : b)),
            }
          : e,
      ),
    }));
  }

  function removeBullet(expIdx: number, bulletIdx: number) {
    mutateContent((c) => ({
      ...c,
      experiences: c.experiences.map((e, i) =>
        i === expIdx
          ? { ...e, bullets: e.bullets.filter((_, j) => j !== bulletIdx) }
          : e,
      ),
    }));
  }

  function addBullet(expIdx: number) {
    mutateContent((c) => ({
      ...c,
      experiences: c.experiences.map((e, i) =>
        i === expIdx ? { ...e, bullets: [...e.bullets, ""] } : e,
      ),
    }));
  }

  function removeSkill(groupIdx: number, skill: string) {
    mutateContent((c) => ({
      ...c,
      skill_groups: c.skill_groups.map((g, i) =>
        i === groupIdx
          ? { ...g, skills: g.skills.filter((s) => s !== skill) }
          : g,
      ),
    }));
  }

  function addSkill(groupIdx: number) {
    const name = (newSkill[groupIdx] ?? "").trim();
    if (!name) return;
    mutateContent((c) => ({
      ...c,
      skill_groups: c.skill_groups.map((g, i) =>
        i === groupIdx && !g.skills.includes(name)
          ? { ...g, skills: [...g.skills, name] }
          : g,
      ),
    }));
    setNewSkill((s) => ({ ...s, [groupIdx]: "" }));
  }

  async function persistContent() {
    await apiFetch(accessToken, `/tailored/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        company_name: company,
        role: role,
        content,
      }),
    });
    setDirty(false);
  }

  async function onSave() {
    setBusy("save");
    try {
      await persistContent();
      toast.success("Saved");
      router.refresh();
    } catch (error) {
      toast.error("Couldn't save", { description: describeApiError(error) });
    } finally {
      setBusy(null);
    }
  }

  async function onExport() {
    setBusy("export");
    try {
      // Export renders the stored snapshot — persist edits first so a
      // failed save can never produce a stale document.
      if (dirty) {
        await persistContent();
        router.refresh();
      }
      const res = (await apiFetch(accessToken, `/tailored/${id}/export`, {
        method: "POST",
      })) as ExportTailoredResponse;
      window.open(res.url, "_blank", "noopener,noreferrer");
    } catch (error) {
      toast.error(describeApiError(error));
    } finally {
      setBusy(null);
    }
  }

  async function onDelete() {
    setBusy("delete");
    try {
      await apiFetch(accessToken, `/tailored/${id}`, { method: "DELETE" });
      toast.success("Tailored resume deleted");
      router.push("/tailored");
    } catch (error) {
      toast.error(describeApiError(error));
      setBusy(null);
      setConfirmDelete(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-semibold tracking-[-0.03em]">
            Tailored Resume
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Edit the tailored content, then export it as a document.
          </p>
        </div>
        <Link
          href="/tailored"
          className="inline-flex shrink-0 items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Tailored resumes
        </Link>
      </header>

      {!contentReadable && (
        <Card className="bg-amber-500/5 ring-amber-500/30">
          <CardContent className="pt-6 text-sm text-amber-200">
            We couldn&apos;t read this saved version. You can still fill in the
            fields below and save to replace it.
          </CardContent>
        </Card>
      )}

      {/* Job details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Job</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                Company
              </label>
              <Input
                value={company}
                onChange={(e) => {
                  setCompany(e.target.value);
                  setDirty(true);
                }}
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                Role
              </label>
              <Input
                value={role}
                onChange={(e) => {
                  setRole(e.target.value);
                  setDirty(true);
                }}
                className={inputClass}
              />
            </div>
          </div>
          <details className="text-sm">
            <summary className="cursor-pointer text-zinc-500 hover:text-zinc-300">
              Job Description
            </summary>
            <p className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950/50 p-3 whitespace-pre-wrap text-zinc-400">
              {jobDescription}
            </p>
          </details>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={content.summary ?? ""}
            onChange={(e) =>
              mutateContent((c) => ({
                ...c,
                summary: e.target.value || null,
              }))
            }
            placeholder="No summary. The exported resume won't have one."
            className={`min-h-24 ${inputClass}`}
          />
        </CardContent>
      </Card>

      {/* Experiences */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Experience</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {content.experiences.map((exp, ei) => (
            <div key={ei} className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-medium text-zinc-100">
                  {exp.title}
                  {exp.company_name && (
                    <span className="text-zinc-400"> · {exp.company_name}</span>
                  )}
                </span>
                <span className="shrink-0 text-xs text-zinc-500">
                  {fmtDate(exp.start_date)} – {fmtDate(exp.end_date)}
                </span>
              </div>
              <Input
                value={exp.location ?? ""}
                onChange={(e) => setLocation(ei, e.target.value)}
                aria-label="Location"
                placeholder="Location (e.g. Remote or City, ST)"
                className={`h-7 sm:max-w-72 ${inputClass}`}
              />
              {exp.bullets.map((bullet, bi) => (
                <div key={bi} className="flex items-start gap-2">
                  <Textarea
                    value={bullet}
                    onChange={(e) => setBullet(ei, bi, e.target.value)}
                    className={`min-h-12 flex-1 ${inputClass}`}
                  />
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    aria-label="Remove Bullet"
                    onClick={() => removeBullet(ei, bi)}
                    className="mt-1 text-zinc-500 hover:text-red-300"
                  >
                    <X />
                  </Button>
                </div>
              ))}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => addBullet(ei)}
                className="self-start text-zinc-400 hover:text-zinc-200"
              >
                <Plus /> Add Bullet
              </Button>
            </div>
          ))}
          {content.experiences.length === 0 && (
            <p className="text-sm text-zinc-500">No experiences saved.</p>
          )}
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Skills</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {content.skill_groups.map((group, gi) => (
            <div key={gi}>
              {group.category !== null && (
                <p className="mb-1.5 text-xs font-medium tracking-wide text-zinc-500 uppercase">
                  {group.category}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-2">
                {group.skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 rounded-md border border-brand-500/30 bg-brand-500/10 px-2 py-0.5 text-sm text-brand-200"
                  >
                    {skill}
                    <button
                      type="button"
                      aria-label={`Remove ${skill}`}
                      onClick={() => removeSkill(gi, skill)}
                      className="text-brand-300/60 hover:text-brand-100"
                    >
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
                <span className="inline-flex items-center gap-1">
                  <Input
                    value={newSkill[gi] ?? ""}
                    onChange={(e) =>
                      setNewSkill((s) => ({ ...s, [gi]: e.target.value }))
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addSkill(gi);
                      }
                    }}
                    placeholder="Add…"
                    className={`h-6 w-24 px-2 text-xs ${inputClass}`}
                  />
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    aria-label="Add Skill"
                    onClick={() => addSkill(gi)}
                    className="text-zinc-500 hover:text-zinc-200"
                  >
                    <Plus />
                  </Button>
                </span>
              </div>
            </div>
          ))}
          {content.skill_groups.length === 0 && (
            <p className="text-sm text-zinc-500">No skills saved.</p>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setConfirmDelete(true)}
          disabled={busy !== null}
          className="text-zinc-500 hover:text-red-300"
        >
          <Trash2 /> Delete
        </Button>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={onSave}
            disabled={busy !== null}
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
          >
            {busy === "save" ? <Loader2 className="animate-spin" /> : <Save />}{" "}
            Save Changes
          </Button>
          <Button
            onClick={onExport}
            disabled={busy !== null}
          >
            {busy === "export" ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Download />
            )}{" "}
            Export
          </Button>
        </div>
      </div>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Delete Tailored Resume?
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              This removes the saved resume and its generated document
              permanently.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfirmDelete(false)}
              disabled={busy !== null}
              className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={onDelete}
              disabled={busy !== null}
              className="border-0 bg-red-600 text-white hover:bg-red-500"
            >
              {busy === "delete" ? (
                <Loader2 className="animate-spin" />
              ) : null}{" "}
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
