import queue
import threading
from dataclasses import dataclass
from psycopg.rows import class_row
from pydantic import BaseModel
from typing import Any

from ..pg import pg_pool
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner



class FetchSuggestionRow(BaseModel):
    company_name: str
    description: str | None
    start_date: str
    end_date: str | None
    title: str
    bullet_id: int
    bullet: str


class SuggestionsRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        try:
            if not self.job_data:
                raise RunnerError("Job data is required")

            if not isinstance(self.job_data, dict):
                raise TypeError("Job data must be a dictionary")

            session_id = self.job_data.get("session_id")
            if not session_id:
                raise RunnerError("Got job with no session_id")

            with pg_pool.connection() as conn, conn.cursor(row_factory=class_row(FetchSuggestionRow)) as cursor:
                r = cursor.execute(
                    """
                    SELECT
                        ue.company_name,
                        ue.description,
                        ue.start_date,
                        ue.end_date,
                        ue.title,
                        ub.id as bullet_id,
                        ub.bullet
                    FROM user_suggestion us
                    JOIN user_base_experience ue ON ue.id = us.experience_id
                    join user_base_experience_bullet ub on ub.user_experience_id = ue.id
                    WHERE us.id = %s
                    and (us.bullet_id is null or ub.id = us.bullet_id)
                    """,
                    [session_id],
                )
                result = r.fetchall()
                if not result:
                    raise RunnerError("Session not found")

                # For now let's just put a dummy question in the table
                print(result)

                cursor.execute(
                    """
                    UPDATE
                        user_suggestion
                    SET
                        pending_question = 'Is this, or is this not a dummy question?',
                        status = 'WAITING_FOR_INPUT'
                    WHERE id = %s
                    """,
                    [session_id]
                )

            


        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return
