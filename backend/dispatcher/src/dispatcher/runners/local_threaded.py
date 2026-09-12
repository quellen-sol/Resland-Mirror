import os
import queue
import threading
from typing import Any

import puremagic
from shared.pg import get_pg_client
from shared.s3 import get_s3_client

from ..agents.resume_parser import build_agent
from ..doc_parsers.docx import parse_docx
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PG_URL,
    S3_RESUME_BUCKET,
)
from .generic import JobHandle, JobRunner


class LocalThreadedJobHandle(JobHandle):
    thread: threading.Thread
    queue: queue.Queue

    def __init__(self, job_data: Any, thread: threading.Thread, queue: queue.Queue):
        super().__init__(job_data)
        self.thread = thread
        self.queue = queue

    def poll(self) -> str:
        # See if exception was thrown, return FAILED
        try:
            _, e = self.queue.get_nowait()
            print(f"Exception was thrown from job with data {self.job_data}: {e}")
        except queue.Empty:
            pass
        else:
            return "FAILED"

        # If not, see if thread is alive, and if so return PROCESSING
        # If not, then COMPLETED
        if self.thread.is_alive():
            return "PROCESSING"
        else:
            return "COMPLETED"


class LocalThreadJobRunner(JobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def run(self) -> JobHandle:
        q = queue.Queue()
        t = threading.Thread(target=self.task, args=(q,))
        t.start()
        return LocalThreadedJobHandle(self.job_data, t, q)

    def task(self, queue: queue.Queue):
        try:
            if not self.job_data:
                raise ValueError("Job data is required")

            if not isinstance(self.job_data, dict):
                raise TypeError("Job data must be a dictionary")

            print("Creating S3 Client")
            s3_client = get_s3_client(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
            pg_client = get_pg_client(PG_URL)

            if not self.job_data.get("job_id"):
                raise ValueError("Job ID is required")
            job_id = self.job_data["job_id"]

            # Get user info from db
            user_result = pg_client.execute("""
                SELECT id, auth0Id from "user" where id = $1
            """, [self.job_data["user_id"]])
            if not user_result:
                raise ValueError("User not found")
            user_id = user_result[0]["id"]
            auth0_id = user_result[0]["auth0Id"]

            # Pull document from s3
            if not self.job_data.get("s3_key"):
                raise ValueError("S3 key is required")
            s3_key = self.job_data["s3_key"]
            print(f"Pulling document from S3: {s3_key}")
            s3_response = s3_client.get_object(
                Bucket=S3_RESUME_BUCKET, Key=s3_key
            )
            if not s3_response:
                raise ValueError("No response from S3")
            print(f"S3 response: {s3_response}")
            # Parse based on filetype with puremagic
            body = s3_response["Body"]
            if not body:
                raise ValueError("No body found in S3 response")
            print("Reading body from S3 response...")
            body_data = body.read()
            file_type = puremagic.from_string(body_data)
            print(f"File type: {file_type}")
            parsed_text: str | None = None
            match file_type:
                case '.docx':
                    parsed_text = parse_docx(body_data)
                case _:
                    raise TypeError("Unsupported file type")

            # Give text to agent to parse
            agent_result = build_agent()
            agent = agent_result.agent
            profile_queue = agent_result.profile_queue

            print("Invoking agent...")
            agent.invoke({"messages": [{"role": "user", "content": f"""Parse this document and extract the candidate's information.
            Document:
            ```
            {parsed_text}
            ```"""}]})
            print("Agent invoked successfully")

            # Agent will have sent results here, then we write to pg
            if not profile_queue.empty():
                profile = profile_queue.get()
                # Upsert all relevant info to pg
                pg_client.execute("""
                    INSERT INTO "user" ("auth0Id", "fullName", "email", "phone", "location")
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT ("auth0Id") DO UPDATE SET
                        "fullName" = EXCLUDED."fullName",
                        "email" = EXCLUDED."email",
                        "phone" = EXCLUDED."phone",
                        "location" = EXCLUDED."location"
                """, [auth0_id, profile.basic_info.name, profile.basic_info.email, profile.basic_info.phone, profile.basic_info.location])
            else:
                print("No profile found in queue - this is unexpected")

        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return
