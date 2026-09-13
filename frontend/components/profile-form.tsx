"use client";

import { useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface SocialLinkForm {
  type: "LINKEDIN" | "GITHUB" | "WEBSITE";
  link: string;
}

export interface ExperienceForm {
  companyName: string;
  title: string;
  startDate: string;
  endDate: string;
  description: string;
  bulletsText: string;
}

export interface EducationForm {
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startDate: string;
  endDate: string;
  description: string;
}

export interface ProjectForm {
  name: string;
  link: string;
  description: string;
  startDate: string;
  endDate: string;
}

export interface ProfileFormValues {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  socialLinks: SocialLinkForm[];
  skills: string[];
  experiences: ExperienceForm[];
  education: EducationForm[];
  projects: ProjectForm[];
}

export const emptyProfileValues: ProfileFormValues = {
  fullName: "",
  email: "",
  phone: "",
  location: "",
  socialLinks: [],
  skills: [],
  experiences: [
    {
      companyName: "",
      title: "",
      startDate: "",
      endDate: "",
      description: "",
      bulletsText: "",
    },
  ],
  education: [],
  projects: [],
};

const inputCls =
  "border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-purple-500 focus-visible:ring-purple-500/30";
const labelCls = "text-zinc-300";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className={labelCls}>
        {label}
        {required && <span className="text-purple-400"> *</span>}
      </Label>
      {children}
    </div>
  );
}

function DateField({
  label,
  required,
  value,
  onChange,
}: {
  label: string;
  required?: boolean;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <Field label={label} required={required}>
      <Input
        type="text"
        placeholder="e.g. Jan 2020"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls}
      />
    </Field>
  );
}

function AddButton({
  onClick,
  children,
}: {
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
      onClick={onClick}
    >
      <Plus /> {children}
    </Button>
  );
}

function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      className="self-end text-zinc-500 hover:text-red-400"
    >
      <Trash2 /> Remove
    </Button>
  );
}

const emptyExperience: ExperienceForm = {
  companyName: "",
  title: "",
  startDate: "",
  endDate: "",
  description: "",
  bulletsText: "",
};

const emptyEducation: EducationForm = {
  institution: "",
  degree: "",
  fieldOfStudy: "",
  startDate: "",
  endDate: "",
  description: "",
};

const emptyProject: ProjectForm = {
  name: "",
  link: "",
  description: "",
  startDate: "",
  endDate: "",
};

export default function ProfileForm({
  initial,
  pending,
  submitLabel,
  onSubmit,
}: {
  initial?: Partial<ProfileFormValues>;
  pending?: boolean;
  submitLabel: string;
  onSubmit: (data: ProfileFormValues) => void;
}) {
  const [values, setValues] = useState<ProfileFormValues>({
    ...emptyProfileValues,
    ...initial,
  });
  const [skillDraft, setSkillDraft] = useState("");

  function set<K extends keyof ProfileFormValues>(
    key: K,
    value: ProfileFormValues[K],
  ) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function updateAt<T>(
    key: "socialLinks" | "experiences" | "education" | "projects",
    index: number,
    patch: Partial<T>,
  ) {
    setValues((v) => ({
      ...v,
      [key]: v[key].map((item, i) =>
        i === index ? { ...item, ...patch } : item,
      ),
    }));
  }

  function removeAt(
    key: "socialLinks" | "experiences" | "education" | "projects",
    index: number,
  ) {
    setValues((v) => ({ ...v, [key]: v[key].filter((_, i) => i !== index) }));
  }

  function addSkill() {
    const name = skillDraft.trim();
    if (name) {
      set("skills", [...values.skills, name]);
      setSkillDraft("");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Contact */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Contact</h3>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <Field label="Full name">
            <Input
              value={values.fullName}
              onChange={(e) => set("fullName", e.target.value)}
              className={inputCls}
            />
          </Field>
          <Field label="Email">
            <Input
              type="email"
              value={values.email}
              onChange={(e) => set("email", e.target.value)}
              className={inputCls}
            />
          </Field>
          <Field label="Phone">
            <Input
              value={values.phone}
              onChange={(e) => set("phone", e.target.value)}
              className={inputCls}
            />
          </Field>
          <Field label="Location">
            <Input
              value={values.location}
              onChange={(e) => set("location", e.target.value)}
              placeholder="City, Country"
              className={inputCls}
            />
          </Field>
        </div>
      </section>

      {/* Social links */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Links</h3>
        <div className="mt-3 flex flex-col gap-3">
          {values.socialLinks.map((link, i) => (
            <div key={i} className="flex items-end gap-2">
              <Field label="Type">
                <Select
                  value={link.type}
                  onValueChange={(v) =>
                    updateAt<SocialLinkForm>("socialLinks", i, {
                      type: v as SocialLinkForm["type"],
                    })
                  }
                >
                  <SelectTrigger className="w-32 border-zinc-700 bg-zinc-950/50 text-zinc-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="border-zinc-700 bg-zinc-900 text-zinc-200">
                    <SelectItem value="LINKEDIN">LinkedIn</SelectItem>
                    <SelectItem value="GITHUB">GitHub</SelectItem>
                    <SelectItem value="WEBSITE">Website</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <div className="flex-1">
                <Field label="URL">
                  <Input
                    value={link.link}
                    onChange={(e) =>
                      updateAt<SocialLinkForm>("socialLinks", i, {
                        link: e.target.value,
                      })
                    }
                    placeholder="https://…"
                    className={inputCls}
                  />
                </Field>
              </div>
              <RemoveButton
                onClick={() => removeAt("socialLinks", i)}
              />
            </div>
          ))}
          <AddButton
            onClick={() =>
              set("socialLinks", [
                ...values.socialLinks,
                { type: "LINKEDIN", link: "" },
              ])
            }
          >
            Add link
          </AddButton>
        </div>
      </section>

      <Separator className="bg-zinc-800" />

      {/* Skills */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Skills</h3>
        <div className="mt-3 flex gap-2">
          <Input
            value={skillDraft}
            onChange={(e) => setSkillDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addSkill();
              }
            }}
            placeholder="e.g. TypeScript — press Enter to add"
            className={inputCls}
          />
          <AddButton onClick={addSkill}>Add</AddButton>
        </div>
        {values.skills.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {values.skills.map((skill, i) => (
              <span
                key={`${skill}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-sm text-purple-200"
              >
                {skill}
                <button
                  type="button"
                  onClick={() =>
                    set(
                      "skills",
                      values.skills.filter((_, j) => j !== i),
                    )
                  }
                  className="text-purple-300/60 hover:text-purple-200"
                  aria-label={`Remove ${skill}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </section>

      <Separator className="bg-zinc-800" />

      {/* Work experience */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Work experience</h3>
        <div className="mt-3 flex flex-col gap-4">
          {values.experiences.map((exp, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Company" required>
                  <Input
                    value={exp.companyName}
                    onChange={(e) =>
                      updateAt<ExperienceForm>("experiences", i, {
                        companyName: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <Field label="Title" required>
                  <Input
                    value={exp.title}
                    onChange={(e) =>
                      updateAt<ExperienceForm>("experiences", i, {
                        title: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <DateField
                  label="Start date"
                  required
                  value={exp.startDate}
                  onChange={(v) =>
                    updateAt<ExperienceForm>("experiences", i, {
                      startDate: v,
                    })
                  }
                />
                <DateField
                  label="End date"
                  value={exp.endDate}
                  onChange={(v) =>
                    updateAt<ExperienceForm>("experiences", i, { endDate: v })
                  }
                />
              </div>
              <Field label="Description">
                <Textarea
                  value={exp.description}
                  onChange={(e) =>
                    updateAt<ExperienceForm>("experiences", i, {
                      description: e.target.value,
                    })
                  }
                  className={inputCls}
                />
              </Field>
              <Field label="Highlights (one per line)">
                <Textarea
                  value={exp.bulletsText}
                  onChange={(e) =>
                    updateAt<ExperienceForm>("experiences", i, {
                      bulletsText: e.target.value,
                    })
                  }
                  placeholder={"Led a team of 5\nShipped feature X"}
                  className={inputCls}
                />
              </Field>
              {values.experiences.length > 1 && (
                <RemoveButton
                  onClick={() => removeAt("experiences", i)}
                />
              )}
            </div>
          ))}
          <AddButton
            onClick={() =>
              set("experiences", [...values.experiences, { ...emptyExperience }])
            }
          >
            Add experience
          </AddButton>
        </div>
      </section>

      <Separator className="bg-zinc-800" />

      {/* Education */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Education</h3>
        <div className="mt-3 flex flex-col gap-4">
          {values.education.map((edu, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Institution" required>
                  <Input
                    value={edu.institution}
                    onChange={(e) =>
                      updateAt<EducationForm>("education", i, {
                        institution: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <Field label="Degree" required>
                  <Input
                    value={edu.degree}
                    onChange={(e) =>
                      updateAt<EducationForm>("education", i, {
                        degree: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <Field label="Field of study" required>
                  <Input
                    value={edu.fieldOfStudy}
                    onChange={(e) =>
                      updateAt<EducationForm>("education", i, {
                        fieldOfStudy: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <div className="grid grid-cols-2 gap-3">
                  <DateField
                    label="Start"
                    required
                    value={edu.startDate}
                    onChange={(v) =>
                      updateAt<EducationForm>("education", i, { startDate: v })
                    }
                  />
                  <DateField
                    label="End"
                    value={edu.endDate}
                    onChange={(v) =>
                      updateAt<EducationForm>("education", i, { endDate: v })
                    }
                  />
                </div>
              </div>
              <Field label="Description">
                <Textarea
                  value={edu.description}
                  onChange={(e) =>
                    updateAt<EducationForm>("education", i, {
                      description: e.target.value,
                    })
                  }
                  className={inputCls}
                />
              </Field>
              <RemoveButton onClick={() => removeAt("education", i)} />
            </div>
          ))}
          <AddButton
            onClick={() =>
              set("education", [...values.education, { ...emptyEducation }])
            }
          >
            Add education
          </AddButton>
        </div>
      </section>

      <Separator className="bg-zinc-800" />

      {/* Projects */}
      <section>
        <h3 className="text-sm font-medium text-purple-300">Projects</h3>
        <div className="mt-3 flex flex-col gap-4">
          {values.projects.map((proj, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-lg border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Name" required>
                  <Input
                    value={proj.name}
                    onChange={(e) =>
                      updateAt<ProjectForm>("projects", i, {
                        name: e.target.value,
                      })
                    }
                    className={inputCls}
                  />
                </Field>
                <Field label="Link">
                  <Input
                    value={proj.link}
                    onChange={(e) =>
                      updateAt<ProjectForm>("projects", i, {
                        link: e.target.value,
                      })
                    }
                    placeholder="https://…"
                    className={inputCls}
                  />
                </Field>
                <DateField
                  label="Start date"
                  required
                  value={proj.startDate}
                  onChange={(v) =>
                    updateAt<ProjectForm>("projects", i, { startDate: v })
                  }
                />
                <DateField
                  label="End date"
                  value={proj.endDate}
                  onChange={(v) =>
                    updateAt<ProjectForm>("projects", i, { endDate: v })
                  }
                />
              </div>
              <Field label="Description">
                <Textarea
                  value={proj.description}
                  onChange={(e) =>
                    updateAt<ProjectForm>("projects", i, {
                      description: e.target.value,
                    })
                  }
                  className={inputCls}
                />
              </Field>
              <RemoveButton onClick={() => removeAt("projects", i)} />
            </div>
          ))}
          <AddButton
            onClick={() =>
              set("projects", [...values.projects, { ...emptyProject }])
            }
          >
            Add project
          </AddButton>
        </div>
      </section>

      <Button
        onClick={() => onSubmit(values)}
        disabled={pending}
        className="h-9 self-end border-0 bg-gradient-to-r from-violet-600 to-purple-600 px-6 text-white shadow-lg shadow-purple-950/50 hover:from-violet-500 hover:to-purple-500"
      >
        {pending ? (
          <>
            <Loader2 className="animate-spin" /> Saving…
          </>
        ) : (
          submitLabel
        )}
      </Button>
    </div>
  );
}
