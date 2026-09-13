from pydantic import BaseModel


class UploadResumeResponse(BaseModel):
    job_id: str


class GetJobStatusResponse(BaseModel):
    status: str
