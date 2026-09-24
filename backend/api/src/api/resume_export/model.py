from pydantic import BaseModel


class ExportResumeResponse(BaseModel):
    url: str
    generated_at: str
    regenerated: bool
