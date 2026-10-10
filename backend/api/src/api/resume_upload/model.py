from pydantic import BaseModel

# A resume upload still PENDING/PROCESSING after this long has crashed — the
# API died between recording the job and publishing it, or the dispatcher
# lost it. It stops blocking new uploads (and account deletion) after this.
STALE_UPLOAD_INTERVAL = "30 minutes"


class UploadResumeResponse(BaseModel):
    job_id: str


class GetJobStatusResponse(BaseModel):
    status: str
