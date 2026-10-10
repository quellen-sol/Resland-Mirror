"""resume_upload service — dedup guard, file-type gating, S3+AMQP+job-row
sequence, and job status lookup.

Run: .venv/bin/python -m unittest backend.api.tests.test_resume_upload -v
"""

import io
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import docx
from fastapi import HTTPException, UploadFile

from api.resume_upload import router, service
from api.resume_upload.model import STALE_UPLOAD_INTERVAL
from shared.amqp import RESUME_EXCHANGE_NAME

from .helpers import _Amqp, _Pg, _Result


def _docx_bytes():
    buf = io.BytesIO()
    d = docx.Document()
    d.add_paragraph("Jane Doe — Engineer")
    d.save(buf)
    return buf.getvalue()


def _file(content, filename="resume.docx"):
    return UploadFile(file=io.BytesIO(content), filename=filename)


class UploadResume(unittest.IsolatedAsyncioTestCase):
    async def test_in_flight_job_409(self):
        pg = _Pg([[(1,)]])  # in-flight row found
        with self.assertRaises(HTTPException) as ctx:
            await service.upload_resume(
                _file(_docx_bytes()), "u1", _Amqp(), pg
            )
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_in_flight_check_ignores_crashed_uploads(self):
        # A job row stuck PENDING (the API died before storing its file)
        # mustn't block uploads forever.
        pg = _Pg([[(1,)]])
        with self.assertRaises(HTTPException):
            await service.upload_resume(_file(_docx_bytes()), "u1", _Amqp(), pg)
        query, params = pg.queries[0]
        self.assertIn("created_at > now() - %s::interval", query)
        self.assertEqual(params, ("u1", STALE_UPLOAD_INTERVAL))

    async def test_non_docx_400(self):
        pg = _Pg([[]])  # no in-flight
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
        with self.assertRaises(HTTPException) as ctx:
            await service.upload_resume(_file(png), "u1", _Amqp(), pg)
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_unrecognizable_content_400(self):
        pg = _Pg([[]])
        with patch.object(
            service.puremagic, "from_string", return_value=""
        ):
            with self.assertRaises(HTTPException) as ctx:
                await service.upload_resume(_file(b"???"), "u1", _Amqp(), pg)
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_puremagic_raises_400(self):
        pg = _Pg([[]])
        with patch.object(
            service.puremagic, "from_string", side_effect=ValueError("bad bytes")
        ):
            with self.assertRaises(HTTPException) as ctx:
                await service.upload_resume(_file(b"???"), "u1", _Amqp(), pg)
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_s3_failure_500_and_job_marked_failed(self):
        pg = _Pg([[]])
        s3 = MagicMock()
        s3.upload_fileobj.side_effect = RuntimeError("s3 down")
        amqp = _Amqp()
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            self.assertRaises(HTTPException) as ctx,
        ):
            await service.upload_resume(_file(_docx_bytes()), "u1", amqp, pg)
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(amqp.publisher.published, [])
        # The PENDING row must not linger and block the next upload (or
        # account deletion).
        failed = [p for q, p in pg.queries if "UPDATE user_upload_job" in q]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "FAILED")

    async def test_publish_failure_marks_job_failed(self):
        pg = _Pg([[]])
        amqp = _Amqp()
        amqp.publisher.publish = AsyncMock(side_effect=RuntimeError("amqp down"))
        with (
            patch.object(service, "get_s3_client", return_value=MagicMock()),
            self.assertRaises(RuntimeError),
        ):
            await service.upload_resume(_file(_docx_bytes()), "u1", amqp, pg)
        failed = [p for q, p in pg.queries if "UPDATE user_upload_job" in q]
        self.assertEqual(failed[0][0], "FAILED")

    async def test_happy_path_inserts_then_uploads_then_publishes(self):
        pg = _Pg([[], _Result()])  # no in-flight, then INSERT
        s3 = MagicMock()
        order = []
        # The job row must exist before the file does: an account deletion
        # racing the upload then either sees the job (409) or the insert
        # fails first — never a file left behind in S3.
        s3.upload_fileobj.side_effect = lambda *a: order.append(
            ("s3", len(pg.queries))
        )
        amqp = _Amqp(order)
        with patch.object(service, "get_s3_client", return_value=s3):
            resp = await service.upload_resume(
                _file(_docx_bytes()), "u1", amqp, pg
            )
        self.assertTrue(resp.job_id)
        insert_at = next(
            i for i, (q, _) in enumerate(pg.queries) if "INSERT INTO user_upload_job" in q
        )
        self.assertEqual(order, [("s3", insert_at + 1), "publish"])
        key = s3.upload_fileobj.call_args.args[2]
        self.assertEqual(key, "resumes/u1/resume_doc.docx")
        self.assertEqual(amqp.calls, [(RESUME_EXCHANGE_NAME, "#")])
        params = pg.queries[insert_at][1]
        self.assertEqual(params[0], resp.job_id)
        self.assertEqual(params[1], "u1")
        self.assertEqual(params[3], "PENDING")

    async def test_pdf_accepted_and_stored_as_pdf(self):
        pg = _Pg([[], _Result()])
        s3 = MagicMock()
        amqp = _Amqp()
        pdf = b"%PDF-1.4\n" + b"\x00" * 64
        with patch.object(service, "get_s3_client", return_value=s3):
            resp = await service.upload_resume(
                _file(pdf, filename="resume.pdf"), "u1", amqp, pg
            )
        self.assertTrue(resp.job_id)
        key = s3.upload_fileobj.call_args.args[2]
        self.assertEqual(key, "resumes/u1/resume_doc.pdf")
        self.assertEqual(amqp.calls, [(RESUME_EXCHANGE_NAME, "#")])


class UploadRouterGuards(unittest.IsolatedAsyncioTestCase):
    async def test_missing_filename_400(self):
        f = UploadFile(file=io.BytesIO(b"x"), filename=None)
        with self.assertRaises(HTTPException) as ctx:
            await router.upload_initial_resume(f, "u1", _Amqp(), _Pg())
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_oversized_file_413(self):
        big = MagicMock()
        big.seek = MagicMock()
        big.tell = MagicMock(return_value=100_000_001)
        f = UploadFile(file=big, filename="big.docx")
        with self.assertRaises(HTTPException) as ctx:
            await router.upload_initial_resume(f, "u1", _Amqp(), _Pg())
        self.assertEqual(ctx.exception.status_code, 413)

    async def test_delegates_to_service(self):
        f = _file(_docx_bytes())
        with (
            patch.object(
                router.service,
                "upload_resume",
                new=AsyncMock(return_value="ok"),
            ) as svc,
        ):
            resp = await router.upload_initial_resume(
                f, "u1", _Amqp(), _Pg()
            )
        self.assertEqual(resp, "ok")
        svc.assert_awaited_once()


class CheckJobStatus(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_job_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.check_job_status("j1", _Pg([[]]))
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_status_returned(self):
        resp = await service.check_job_status("j1", _Pg([[("COMPLETED",)]]))
        self.assertEqual(resp.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
