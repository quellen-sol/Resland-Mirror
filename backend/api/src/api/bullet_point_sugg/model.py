from pydantic import BaseModel, Field


class StartSuggestionRequest(BaseModel):
    experience_id: int
    bullet_id: int | None = None
    prompt: str | None = None
    # Must be an enabled model_pricing id; null = system default.
    model: str | None = None


class AnswerRequest(BaseModel):
    text: str


class AcceptChoice(BaseModel):
    bullet_id: int
    # Index into that bullet's suggested options.
    option: int = Field(ge=0)


class AcceptSuggestionRequest(BaseModel):
    # Bullets left out keep their current text.
    choices: list[AcceptChoice]


class StartSuggestionResponse(BaseModel):
    session_id: str


class SuggestionStatusResponse(BaseModel):
    status: str
    pending_question: str | None = None
    result: str | None = None
