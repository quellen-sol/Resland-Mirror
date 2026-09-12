import io
import os
import uuid

from fastapi import APIRouter, HTTPException, Request, UploadFile
from shared.amqp import AMQPJob, RESUME_EXCHANGE_NAME
from shared.pg import get_pg_client

router = APIRouter()

@router.post("/upload-initial-resume", status_code=200)
async def upload_initial_resume(file: UploadFile, user_id: int, req: Request):
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

    bucket = os.getenv("S3_RESUME_BUCKET")
    if not bucket:
        raise HTTPException(
            status_code=500, detail="S3_RESUME_BUCKET is not configured"
        )

    job_id = uuid.uuid4()
    obj_key = f"tmp/resumes/{job_id}-{file.filename}"
    try:
        req.app.state.s3_client.upload_fileobj(io.BytesIO(file_content), bucket, obj_key)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to upload file to S3"
        ) from e

    amqp_publisher = await req.app.state.amqp_client.get_publisher(RESUME_EXCHANGE_NAME, "#")
    job = AMQPJob(s3_key=obj_key, job_id=str(job_id))
    await amqp_publisher.publish(job.as_message())

    pg_client = get_pg_client(os.getenv("PG_URL"))
    pg_client.execute(
        'INSERT INTO user_upload_job (id, "userId", status) VALUES (%s, %s, %s)',
        (str(job_id), user_id, "PENDING"),
    )
    pg_client.close()

    return {"job_id": str(job_id)}

@router.get("/check-job-status/{job_id}", status_code=200)
async def check_job_status(job_id: str, req: Request):
    pg_client = get_pg_client(os.getenv("PG_URL"))
    result = pg_client.execute(
        'SELECT status FROM user_upload_job WHERE id = %s',
        (job_id,)
    )
    pg_client.close()
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": result[0][0]}
