import queue
import threading
from typing import Any

import puremagic
from dispatcher.runners.local_threaded import LocalThreadJobRunner
from shared.docgen import capture_format_profile, capture_format_profile_pdf
from shared.pg import get_pg_client
from shared.s3 import get_s3_client

from ..agents.docx_parser import agent_parse_docx
from ..agents.pdf_parser import agent_parse_pdf
from ..doc_parsers.docx import parse_docx
from ..doc_parsers.pdf import parse_pdf
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    PG_URL,
    S3_RESUME_BUCKET,
)
from .db_ops import upsert_resume_format, upsert_user_profile
from .generic import RunnerError


class ResumeRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        try:
            if not self.job_data:
                raise RunnerError("Job data is required")

            if not isinstance(self.job_data, dict):
                raise TypeError("Job data must be a dictionary")

            print("Creating S3 Client")
            s3_client = get_s3_client(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )

            with get_pg_client(PG_URL) as pg_client:
                if not self.job_data.get("job_id"):
                    raise RunnerError("Job ID is required")

                # user_id in the job message is the Auth0 sub — the user PK now
                user_id = self.job_data["user_id"]
                user_result = pg_client.execute(
                    """
                        SELECT auth0_id from "user" where auth0_id = %s
                    """,
                    [user_id],
                ).fetchone()
                if not user_result:
                    # The account was deleted after the upload was queued.
                    # End cleanly so the message is acked, not dead-lettered.
                    print(
                        f"Resume job {self.job_data['job_id']}: account gone, dropped"
                    )
                    return

                # Pull document from s3
                if not self.job_data.get("s3_key"):
                    raise RunnerError("S3 key is required")
                s3_key = self.job_data["s3_key"]
                print(f"Pulling document from S3: {s3_key}")
                s3_response = s3_client.get_object(Bucket=S3_RESUME_BUCKET, Key=s3_key)
                if not s3_response:
                    raise RunnerError("No response from S3")
                print(f"S3 response: {s3_response}")
                # Parse based on filetype with puremagic
                body = s3_response["Body"]
                if not body:
                    raise RunnerError("No body found in S3 response")
                print("Reading body from S3 response...")
                body_data = body.read()
                file_type = puremagic.from_string(body_data)
                print(f"File type: {file_type}")
                profile_queue = None
                source_doc = None
                capture_fmt = None

                # Parse document based on file type
                match file_type:
                    case ".docx":
                        source_doc = parse_docx(body_data)
                        profile_queue = agent_parse_docx(source_doc)
                        capture_fmt = capture_format_profile
                    case ".pdf":
                        source_doc = parse_pdf(body_data)
                        if not source_doc.lines:
                            raise RunnerError(
                                "PDF has no extractable text (scanned or image-only?)"
                            )
                        profile_queue = agent_parse_pdf(source_doc)
                        capture_fmt = capture_format_profile_pdf
                    case _:
                        raise RunnerError("Unsupported file type")

                # Agent will have sent results here, then we write to pg
                if profile_queue.empty():
                    raise RunnerError("No profile found in queue")
                profile = profile_queue.get()
                # Upsert all relevant info to pg
                if not upsert_user_profile(pg_client, user_id, profile):
                    print(
                        f"Resume job {self.job_data['job_id']}: account deleted"
                        " while parsing, dropped"
                    )
                    return

                # Capture the layout so the resume can be regenerated later
                if source_doc is not None and capture_fmt is not None:
                    fmt = capture_fmt(source_doc, profile)
                    upsert_resume_format(
                        pg_client, user_id, fmt, self.job_data["job_id"]
                    )

        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return
