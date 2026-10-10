from pydantic import BaseModel, Field, field_validator
from shared.memory import MAX_FACT_CHARS, MAX_MEMORY_FACTS, MAX_TOPIC_CHARS


class MemoryFact(BaseModel):
    id: int
    topic: str
    content: str


class MemoryFactItem(MemoryFact):
    source: str
    updated_at: str


class MemoryListResponse(BaseModel):
    # Grouped by topic, oldest first within one — the order the agents read.
    facts: list[MemoryFactItem]


class NewMemoryFact(BaseModel):
    topic: str = Field(min_length=1, max_length=MAX_TOPIC_CHARS)
    content: str = Field(min_length=1, max_length=MAX_FACT_CHARS)
    # A bank fact this one corrects or extends; it's rewritten in place.
    replaces_id: int | None = None

    @field_validator("topic", "content", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


class RememberRequest(BaseModel):
    facts: list[NewMemoryFact] = Field(min_length=1, max_length=MAX_MEMORY_FACTS)


class RememberResponse(BaseModel):
    # Facts now in the bank (newly stored, rewritten, or already there).
    saved: list[MemoryFact]
    # New facts turned away because the bank is at MAX_MEMORY_FACTS.
    full: int = 0
