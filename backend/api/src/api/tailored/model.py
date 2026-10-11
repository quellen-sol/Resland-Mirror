from typing import Annotated

from pydantic import BaseModel, Field

MAX_JOB_DESCRIPTION_CHARS = 10_000
MAX_TAILORED_FIELD_CHARS = 200
MAX_TAILORED_BULLET_CHARS = 2_000
MAX_TAILORED_ITEMS = 200


# Editable snapshot of a tailored resume — the sections the tailor agent owns.
# Header/education/projects stay sourced from the base profile at export time.
class TailoredExperienceContent(BaseModel):
    company_name: str = ""
    title: str = ""
    # Snapshots saved before experiences had a location load as None.
    location: str | None = None
    start_date: str = ""
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list, max_length=MAX_TAILORED_ITEMS)


class TailoredSkillGroupContent(BaseModel):
    category: str | None = None
    skills: list[str] = Field(default_factory=list, max_length=MAX_TAILORED_ITEMS)


class TailoredContent(BaseModel):
    summary: str | None = None
    experiences: list[TailoredExperienceContent] = Field(
        default_factory=list, max_length=MAX_TAILORED_ITEMS
    )
    skill_groups: list[TailoredSkillGroupContent] = Field(
        default_factory=list, max_length=MAX_TAILORED_ITEMS
    )


# Shape of user_tailor_run.result written by the dispatcher's tailor agent.
class TailorRunResultBullet(BaseModel):
    bullet_id: int
    text: str = Field(max_length=MAX_TAILORED_BULLET_CHARS)


class TailorRunResultExperience(BaseModel):
    experience_id: int
    bullets: list[TailorRunResultBullet]


class TailorRunResult(BaseModel):
    summary: str | None = None
    experiences: list[TailorRunResultExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


# A tailored resume written outside the tailor agent (the personal MCP
# server). Same shape as a run result, except bullets are free text: the
# experiences point at base profile ids so the header fields come from the
# profile, and skills are grouped by their base category on save.
TailoredBulletText = Annotated[str, Field(max_length=MAX_TAILORED_BULLET_CHARS)]


class CreateTailoredExperience(BaseModel):
    experience_id: int
    bullets: list[TailoredBulletText] = Field(
        default_factory=list, max_length=MAX_TAILORED_ITEMS
    )


class CreateTailoredRequest(BaseModel):
    company_name: str | None = Field(default=None, max_length=MAX_TAILORED_FIELD_CHARS)
    role: str | None = Field(default=None, max_length=MAX_TAILORED_FIELD_CHARS)
    job_description: str = Field(min_length=1, max_length=MAX_JOB_DESCRIPTION_CHARS)
    summary: TailoredBulletText | None = None
    experiences: list[CreateTailoredExperience] = Field(
        min_length=1, max_length=MAX_TAILORED_ITEMS
    )
    skills: list[str] = Field(default_factory=list, max_length=MAX_TAILORED_ITEMS)


class CreateTailoredResponse(BaseModel):
    id: str


class TailoredResumeListItem(BaseModel):
    id: str
    company_name: str | None = None
    role: str | None = None
    created_at: str
    generated_at: str | None = None


class TailoredResumeResponse(BaseModel):
    id: str
    company_name: str | None = None
    role: str | None = None
    job_description: str
    content: TailoredContent
    created_at: str
    updated_at: str
    generated_at: str | None = None


class UpdateTailoredRequest(BaseModel):
    company_name: str | None = Field(default=None, max_length=MAX_TAILORED_FIELD_CHARS)
    role: str | None = Field(default=None, max_length=MAX_TAILORED_FIELD_CHARS)
    job_description: str | None = Field(
        default=None, min_length=1, max_length=MAX_JOB_DESCRIPTION_CHARS
    )
    content: TailoredContent | None = None


class TailoredListResponse(BaseModel):
    items: list[TailoredResumeListItem]


class ExportTailoredResponse(BaseModel):
    url: str
    generated_at: str
    regenerated: bool
