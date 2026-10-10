"""Account export + deletion: response shapes and the export document spec.

The export document (`data.json` in the archive) is declared here as data,
not assembled ad hoc, so what leaves the system is reviewable in one place
and a test can check every table that references a user is accounted for.
"""

from dataclasses import dataclass

from pydantic import BaseModel


class DeleteAccountResponse(BaseModel):
    ok: bool = True
    # False when Auth0 didn't confirm the login deletion yet: the data is
    # gone and the sweeper finishes the login (see account.sweeper).
    login_deleted: bool = True


# Bumped whenever a section's shape changes, so a reader of an old archive
# knows which layout it holds.
EXPORT_FORMAT_VERSION = 1


@dataclass(frozen=True)
class ExportSection:
    """One top-level list in data.json: the user's rows from `table`.

    `columns` is an allowlist — anything not named (internal bookkeeping,
    our provider costs, the admin flag) never reaches the archive.
    `json_columns` hold JSON stored as text; they're decoded so the export
    nests instead of carrying escaped strings.
    """

    key: str
    table: str
    columns: tuple[str, ...]
    order_by: str
    json_columns: tuple[str, ...] = ()


# Profile columns of the `user` row (exported as `profile`). `site_admin` is
# deliberately absent: it's an internal flag, not the person's data.
PROFILE_COLUMNS = ("full_name", "email", "phone", "location", "summary")
ACCOUNT_COLUMNS = (
    "auth0_id",
    "created_at",
    "has_onboarded",
    "balance_cents",
    "stripe_customer_id",
)

# Tables keyed on user_id, in the order they appear in data.json.
EXPORT_SECTIONS: tuple[ExportSection, ...] = (
    ExportSection("links", "user_social_link", ("id", "type", "link"), "id"),
    ExportSection(
        "experiences",
        "user_base_experience",
        (
            "id",
            "company_name",
            "title",
            "start_date",
            "end_date",
            "description",
            "created_at",
        ),
        "created_at DESC, id",
    ),
    ExportSection(
        "skills",
        "user_base_skill",
        ("id", "name", "category", "sort_order"),
        "sort_order, id",
    ),
    ExportSection(
        "education",
        "user_base_education",
        (
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "description",
        ),
        "id",
    ),
    ExportSection(
        "projects",
        "user_base_project",
        ("id", "name", "link", "description", "start_date", "end_date"),
        "id",
    ),
    ExportSection(
        "resume_format",
        "user_resume_format",
        ("format", "source_job_id", "captured_at"),
        "captured_at",
        json_columns=("format",),
    ),
    ExportSection(
        "generated_resume",
        "user_generated_resume",
        ("template", "generated_at"),
        "generated_at",
    ),
    ExportSection(
        "resume_uploads",
        "user_upload_job",
        ("id", "status", "created_at"),
        "created_at",
    ),
    ExportSection(
        "suggestions",
        "user_suggestion",
        (
            "id",
            "experience_id",
            "bullet_id",
            "model",
            "status",
            "pending_question",
            "result",
            "created_at",
        ),
        "created_at",
        json_columns=("result",),
    ),
    ExportSection(
        "tailor_runs",
        "user_tailor_run",
        (
            "id",
            "company_name",
            "role",
            "job_description",
            "model",
            "status",
            "pending_question",
            "result",
            "created_at",
        ),
        "created_at",
        json_columns=("result",),
    ),
    ExportSection(
        "tailored_resumes",
        "user_tailored_resume",
        (
            "id",
            "tailor_run_id",
            "company_name",
            "role",
            "job_description",
            "content",
            "generated_at",
            "created_at",
            "updated_at",
        ),
        "created_at",
        json_columns=("content",),
    ),
    ExportSection(
        "system_design_sessions",
        "user_system_design_session",
        (
            "id",
            "source",
            "problem_id",
            "tailored_resume_id",
            "company_name",
            "role",
            "job_description",
            "level",
            "model",
            "status",
            "phase",
            "title",
            "prompt",
            "requirements",
            "estimates",
            "diagram",
            "phase_durations",
            "phase_started_at",
            "result",
            "letter_grade",
            "hire_signal",
            "created_at",
            "completed_at",
        ),
        "created_at",
        json_columns=("diagram", "phase_durations", "result"),
    ),
    ExportSection(
        "dsa_progress", "user_dsa_progress", ("topic", "created_at"), "created_at"
    ),
    ExportSection(
        "memory",
        "user_memory_fact",
        ("id", "topic", "content", "source", "created_at", "updated_at"),
        "topic, id",
    ),
    ExportSection(
        "purchases",
        "balance_purchase",
        ("id", "cents", "amount_cents", "currency", "status", "created_at"),
        "created_at",
    ),
    ExportSection(
        "usage",
        "token_usage",
        (
            "id",
            "job_kind",
            "job_id",
            "model",
            "input_tokens",
            "output_tokens",
            "amount_cents",
            "created_at",
        ),
        "created_at",
    ),
)

# Rows owned through a parent rather than a user_id column, nested under
# their parent's entries: bullets under `experiences`, the interview
# transcript under `system_design_sessions`.
BULLET_COLUMNS = ("id", "bullet", "bullet_order", "created_at")
MESSAGE_COLUMNS = ("id", "role", "phase", "content", "created_at")

# Sections that hold at most one row per user — exported as an object (or
# null) instead of a one-element list.
SINGLETON_SECTIONS = frozenset({"resume_format", "generated_resume"})
