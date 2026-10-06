import io
import uuid

import puremagic
from fastapi import HTTPException, UploadFile
from shared.amqp import RESUME_EXCHANGE_NAME, AmqpResumeJob
from shared.s3 import get_s3_client

from ..deps import AmqpClientDep, PgConnection
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_RESUME_BUCKET,
)
from . import model
from .model import STALE_UPLOAD_INTERVAL


async def upload_resume(
    file: UploadFile, user_id: str, amqp_client: AmqpClientDep, pg_conn: PgConnection
):
    async with pg_conn.cursor() as conn:
        # A job older than STALE_UPLOAD_INTERVAL crashed (e.g. the API died
        # after recording it but before storing the file) — don't let it
        # block uploads forever.
        in_flight = await conn.execute(
            "SELECT 1 FROM user_upload_job WHERE user_id = %s"
            " AND status IN ('PENDING', 'PROCESSING')"
            " AND created_at > now() - %s::interval LIMIT 1",
            (user_id, STALE_UPLOAD_INTERVAL),
        )
        in_flight = await in_flight.fetchone()
        if in_flight:
            raise HTTPException(
                status_code=409,
                detail="A resume is already being processed for this user",
            )

    file_content = await file.read()

    try:
        file_type = puremagic.from_string(file_content)
        if not file_type:
            raise HTTPException(status_code=400, detail="Failed to determine file type")

        if file_type not in [".docx", ".pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to determine file type: {e}"
        ) from e

    job_id = uuid.uuid4()
    # Keep the real extension — pdf uploads land here too once supported.
    obj_key = f"resumes/{user_id}/resume_doc{file_type}"

    # The job row goes in before the file: its foreign key makes it wait out
    # (then fail on) an account deletion in progress, and once it exists a
    # deletion sees the upload in flight and refuses. Either way no file can
    # land in S3 after the account's files were swept.
    async with pg_conn.cursor() as conn:
        await conn.execute(
            "INSERT INTO user_upload_job (id, user_id, s3_key, status) VALUES (%s, %s, %s, %s)",
            (str(job_id), user_id, obj_key, "PENDING"),
        )

    try:
        try:
            s3_client = get_s3_client(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
            s3_client.upload_fileobj(
                io.BytesIO(file_content), S3_RESUME_BUCKET, obj_key
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Failed to upload file to S3"
            ) from e

        job = AmqpResumeJob(s3_key=obj_key, job_id=str(job_id), user_id=user_id)
        amqp_publisher = await amqp_client.get_publisher(RESUME_EXCHANGE_NAME, "#")
        await amqp_publisher.publish(job.to_message())
    except BaseException:
        # Nothing will process this job — don't leave it PENDING, where it
        # would block the next upload.
        async with pg_conn.cursor() as conn:
            await conn.execute(
                "UPDATE user_upload_job SET status = %s WHERE id = %s",
                ("FAILED", str(job_id)),
            )
        raise

    return model.UploadResumeResponse(job_id=str(job_id))


async def check_job_status(job_id: str, pg_conn: PgConnection):
    async with pg_conn.cursor() as conn:
        row = await conn.execute(
            "SELECT status FROM user_upload_job WHERE id = %s", (job_id,)
        )
        row = await row.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return model.GetJobStatusResponse(status=row[0])
