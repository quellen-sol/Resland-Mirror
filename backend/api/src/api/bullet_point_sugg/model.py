from pydantic import BaseModel


class StartSuggestionRequest(BaseModel):
    experience_id: int
    bullet_id: int | None = None
    prompt: str | None = None


class GetSuggestionRequest(BaseModel):
    session_id: str


class AnswerRequest(BaseModel):
    text: str
    session_id: str


class StartSuggestionResponse(BaseModel):
    id: str


class SuggestionStatusResponse(BaseModel):
    status: str
    pendingQuestion: str | None = None
    result: str | None = None
