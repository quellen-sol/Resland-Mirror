import io
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from shared.amqp import AMQPClient, AMQPJob
from shared.pg import get_pg_client
from shared.s3 import s3_client

amqp_client = AMQPClient(os.getenv("AMQP_URL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await amqp_client.setup()
    yield
    await amqp_client.close()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/upload-initial-resume", status_code=200)
async def upload_initial_resume(file: UploadFile, user_id: int):
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
        raise HTTPException(status_code=500, detail="S3_RESUME_BUCKET is not configured")

    job_id = uuid.uuid4()
    obj_key = f"tmp/resumes/{job_id}-{file.filename}"
    try:
        s3_client.upload_fileobj(io.BytesIO(file_content), bucket, obj_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3") from e

    amqp_publisher = await amqp_client.get_publisher("test-exchange", "#")
    job = AMQPJob(s3_key=obj_key, job_id=str(job_id))
    await amqp_publisher.publish(job.as_message())

    pg_client = get_pg_client(os.getenv("PG_URL"))
    pg_client.execute("INSERT INTO user_upload_job (id, \"userId\", status) VALUES (%s, %s, %s)", (str(job_id), user_id, "PENDING"))
    pg_client.close()

    return {"job_id": str(job_id)}
