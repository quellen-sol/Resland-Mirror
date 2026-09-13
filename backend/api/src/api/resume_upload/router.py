import os

from api.deps import AmqpClientDep, PgConnection
from fastapi import APIRouter, HTTPException, UploadFile

from ..auth import Auth0UserId
from . import model, service

router = APIRouter()


@router.post("/upload-initial-resume", response_model=model.UploadResumeResponse)
async def upload_initial_resume(
    file: UploadFile,
    user_id: Auth0UserId,
    amqp_client: AmqpClientDep,
    pg_conn: PgConnection,
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Quick check on filesize without dumping it all into memory.
    # This can be handled by an ALB or similar fronting service, of course.
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > 100000000:  # 100MB
        raise HTTPException(status_code=413, detail="File too large")

    return await service.upload_resume(
        file=file, user_id=user_id, amqp_client=amqp_client, pg_conn=pg_conn
    )


@router.get("/check-job-status/{job_id}", response_model=model.GetJobStatusResponse)
async def check_job_status(job_id: str, pg_conn: PgConnection):
    return await service.check_job_status(job_id=job_id, pg_conn=pg_conn)
