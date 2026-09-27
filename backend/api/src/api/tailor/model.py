from pydantic import BaseModel, Field

MAX_JOB_DESCRIPTION_CHARS = 10_000
MAX_TAILOR_FIELD_CHARS = 200


class StartTailorRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=MAX_JOB_DESCRIPTION_CHARS)
    # Target company/role — surfaced to the agent and copied onto the saved
    # tailored resume.
    company_name: str | None = Field(default=None, max_length=MAX_TAILOR_FIELD_CHARS)
    role: str | None = Field(default=None, max_length=MAX_TAILOR_FIELD_CHARS)
    # Must be an enabled model_pricing id; null = system default.
    model: str | None = None


class AnswerRequest(BaseModel):
    text: str


class StartTailorResponse(BaseModel):
    run_id: str
    resumed: bool = False


class TailorStatusResponse(BaseModel):
    run_id: str
    status: str
    job_description: str
    company_name: str | None = None
    role: str | None = None
    pending_question: str | None = None
    result: str | None = None


class SaveTailorResponse(BaseModel):
    tailored_id: str
