from pydantic import BaseModel, Field

MAX_JOB_DESCRIPTION_CHARS = 10_000


class StartTailorRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=MAX_JOB_DESCRIPTION_CHARS)
    # Must be an enabled model_pricing id; null = system default.
    model: str | None = None


class AnswerRequest(BaseModel):
    text: str


class StartTailorResponse(BaseModel):
    run_id: str


class TailorStatusResponse(BaseModel):
    status: str
    pending_question: str | None = None
    result: str | None = None
