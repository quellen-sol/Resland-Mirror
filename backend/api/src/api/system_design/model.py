from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# An Excalidraw scene is mostly coordinates; a busy 45-minute diagram stays
# well under this.
MAX_DIAGRAM_CHARS = 2_000_000
MAX_NOTES_CHARS = 20_000
MAX_MESSAGE_CHARS = 4_000

Level = Literal["MID", "SENIOR", "STAFF"]
Source = Literal["BANK", "JOB"]
TurnAction = Literal["message", "advance", "finish", "retry"]


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    tags: list[str]
    summary: str


class ProblemsResponse(BaseModel):
    problems: list[ProblemSummary]


class StartSystemDesignRequest(BaseModel):
    source: Source
    # BANK: a bank problem id, or null for a random one the user hasn't done.
    problem_id: str | None = Field(default=None, max_length=100)
    # JOB: a saved tailored resume whose job posting seeds the problem.
    tailored_resume_id: str | None = Field(default=None, max_length=100)
    level: Level = "SENIOR"
    # Must be an enabled model_pricing id; null = system default.
    model: str | None = None


class StartSystemDesignResponse(BaseModel):
    session_id: str
    resumed: bool = False


class Workspace(BaseModel):
    """Candidate workspace fields; omitted fields are left as stored."""

    diagram: str | None = Field(default=None, max_length=MAX_DIAGRAM_CHARS)
    requirements: str | None = Field(default=None, max_length=MAX_NOTES_CHARS)
    estimates: str | None = Field(default=None, max_length=MAX_NOTES_CHARS)


class DiagramIssue(BaseModel):
    kind: str
    element_id: str
    message: str


class WorkspaceResponse(BaseModel):
    diagram: str
    requirements: str
    estimates: str
    issues: list[DiagramIssue]


class TurnRequest(BaseModel):
    action: TurnAction
    text: str | None = Field(default=None, max_length=MAX_MESSAGE_CHARS)
    # Saved before the turn so the interviewer sees the latest work.
    workspace: Workspace | None = None
    # Submit the design even though the diagram has unconnected pieces.
    acknowledge_issues: bool = False


class TurnResponse(BaseModel):
    phase: str


class Message(BaseModel):
    id: int
    role: str
    phase: str
    content: str
    created_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    phase: str
    source: str
    level: str
    problem_id: str | None = None
    company_name: str | None = None
    role: str | None = None
    title: str | None = None
    prompt: str | None = None
    notice: str | None = None
    phase_started_at: datetime
    created_at: datetime
    completed_at: datetime | None = None
    # Lets the client correct its clock for the phase timer.
    server_time: datetime
    phase_durations: dict[str, int]
    phase_targets: dict[str, int]
    messages: list[Message]
    letter_grade: str | None = None
    hire_signal: str | None = None
    # The graded report and the interviewer's brief — only once COMPLETED.
    result: dict | None = None
    reference: dict | None = None
