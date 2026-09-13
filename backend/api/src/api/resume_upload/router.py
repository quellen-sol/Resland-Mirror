import io
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from shared.amqp import RESUME_EXCHANGE_NAME, AMQPClient, AMQPJob
from shared.pg import get_pg_client
from shared.s3 import get_s3_client

from ..auth import Auth0UserId
from ..env_vars import (
    AMQP_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PG_URL,
    S3_RESUME_BUCKET,
)

router = APIRouter()


@router.post("/upload-initial-resume", status_code=200)
async def upload_initial_resume(file: UploadFile, user_id: Auth0UserId):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Quick check on filesize without dumping it all into memory.
    # This can be handled by an ALB or similar fronting service, of course.
    file.file.seek(0, os.SEEK_END)  
    size = file.file.tell()
    file.file.seek(0)
    if size > 100000000:  # 100MB
        raise HTTPException(status_code=413, detail="File too large")

    # This is safe to read. Read all bytes
    file_content = await file.read()

    bucket = S3_RESUME_BUCKET
    if not bucket:
        raise HTTPException(
            status_code=500, detail="S3_RESUME_BUCKET is not configured"
        )

    job_id = uuid.uuid4()
    obj_key = f"resumes/{user_id}/resume_doc.unknown"
    try:
        s3_client = get_s3_client(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        s3_client.upload_fileobj(io.BytesIO(file_content), bucket, obj_key)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to upload file to S3"
        ) from e

    pg_client = get_pg_client(PG_URL)
    in_flight = pg_client.execute(
        'SELECT 1 FROM user_upload_job WHERE "userId" = %s AND status IN (\'PENDING\', \'PROCESSING\') LIMIT 1',
        (user_id,),
    ).fetchone()
    if in_flight:
        pg_client.close()
        raise HTTPException(
            status_code=409,
            detail="A resume is already being processed for this user",
        )

    amqp_client = AMQPClient(AMQP_URL)
    await amqp_client.connect()
    amqp_publisher = await amqp_client.get_publisher(RESUME_EXCHANGE_NAME, "#")
    job = AMQPJob(s3_key=obj_key, job_id=str(job_id), user_id=user_id)
    await amqp_publisher.publish(job.as_message())

    pg_client.execute(
        'INSERT INTO user_upload_job (id, "userId", "s3Key", status) VALUES (%s, %s, %s, %s)',
        (str(job_id), user_id, obj_key, "PENDING"),
    )
    pg_client.close()

    return {"job_id": str(job_id)}

@router.get("/check-job-status/{job_id}", status_code=200)
async def check_job_status(job_id: str):
    pg_client = get_pg_client(PG_URL)
    row = pg_client.execute(
        'SELECT status FROM user_upload_job WHERE id = %s',
        (job_id,)
    ).fetchone()
    pg_client.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": row[0]}
