from pydantic import BaseModel


class StartSuggestionRequest(BaseModel):
    experience_id: int
    bullet_id: int | None = None
    prompt: str | None = None
    # Must be an enabled model_pricing id; null = system default.
    model: str | None = None


class AnswerRequest(BaseModel):
    text: str


class StartSuggestionResponse(BaseModel):
    session_id: str


class SuggestionStatusResponse(BaseModel):
    status: str
    pending_question: str | None = None
    result: str | None = None
