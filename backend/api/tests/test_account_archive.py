"""account.archive + the service's pure pieces (filename, Stripe step).

Run: .venv/bin/python -m unittest backend.api.tests.test_account_archive -v
"""

import datetime
import io
import json
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import patch

import stripe

from api.account import archive, service

from .helpers import FakeS3

PREFIX = "resumes/u1/"


def _write(data=None, objects=None, keys=None, identity_note=None):
    s3 = FakeS3(objects or {})
    dest = io.BytesIO()
    included = archive.write_archive(
        dest,
        data=data or {"format_version": 1, "profile": {"full_name": "Jane"}},
        s3=s3,
        bucket="b",
        prefix=PREFIX,
        keys=keys if keys is not None else sorted(s3.objects),
        login_identity_note=identity_note,
    )
    dest.seek(0)
    return zipfile.ZipFile(dest), included


class WriteArchive(unittest.TestCase):
    def test_layout(self):
        objects = {
            f"{PREFIX}resume_doc.pdf": b"%PDF original",
            f"{PREFIX}generated.docx": b"docx",
            f"{PREFIX}tailored/t1.docx": b"tailored",
        }
        zf, included = _write(objects=objects)
        self.assertEqual(
            sorted(zf.namelist()),
            [
                "README.txt",
                "data.json",
                "files/generated.docx",
                "files/resume_doc.pdf",
                "files/tailored/t1.docx",
            ],
        )
        self.assertEqual(
            sorted(included),
            ["files/generated.docx", "files/resume_doc.pdf", "files/tailored/t1.docx"],
        )
        self.assertEqual(zf.read("files/resume_doc.pdf"), b"%PDF original")
        self.assertEqual(
            json.loads(zf.read("data.json")),
            {"format_version": 1, "profile": {"full_name": "Jane"}},
        )

    def test_vanished_object_is_skipped(self):
        # Listed, then deleted before it was read (e.g. a tailored resume
        # deleted mid-export) — the export still completes.
        objects = {f"{PREFIX}generated.docx": b"docx"}
        zf, included = _write(
            objects=objects, keys=[f"{PREFIX}generated.docx", f"{PREFIX}gone.docx"]
        )
        self.assertEqual(included, ["files/generated.docx"])
        self.assertNotIn("files/gone.docx", zf.namelist())

    def test_readme_lists_files_and_exclusions(self):
        zf, _ = _write(objects={f"{PREFIX}resume_doc.docx": b"d"})
        readme = zf.read("README.txt").decode()
        self.assertIn("files/resume_doc.docx", readme)
        self.assertIn("data.json", readme)
        # Says plainly what isn't in here.
        self.assertIn("working state", readme)
        self.assertIn("Stripe", readme)

    def test_readme_without_files(self):
        zf, included = _write(objects={})
        self.assertEqual(included, [])
        self.assertIn("No files", zf.read("README.txt").decode())

    def test_readme_explains_a_missing_login_identity(self):
        with_identity = archive.readme_text(files=[], login_identity_note=None)
        self.assertNotIn("Note:", with_identity)
        for note in (
            archive.IDENTITY_UNAVAILABLE,
            archive.IDENTITY_NOT_FOUND,
            archive.IDENTITY_NOT_FETCHED,
        ):
            readme = archive.readme_text(files=[], login_identity_note=note)
            # Wrapped for a text file, but every word is there.
            self.assertIn(" ".join(note.split()), " ".join(readme.split()))
            self.assertTrue(all(len(line) <= 76 for line in readme.splitlines()))
        # Only a transient failure suggests trying again.
        self.assertIn("again later", archive.IDENTITY_UNAVAILABLE)
        self.assertNotIn("again", archive.IDENTITY_NOT_FOUND)


class ExportFilename(unittest.TestCase):
    def test_dated(self):
        self.assertEqual(
            service.export_filename(datetime.date(2026, 10, 6)),
            "resland-data-2026-10-06.zip",
        )


def _invalid_request(code):
    return stripe.InvalidRequestError("nope", None, code=code)


class _StripeFakes(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def _expire(self, error=None):
        def expire(session_id):
            self.calls.append(("expire", session_id))
            if error:
                raise error

        return expire

    def _retrieve(self, status, payment_status):
        def retrieve(session_id):
            self.calls.append(("retrieve", session_id))
            return SimpleNamespace(status=status, payment_status=payment_status)

        return retrieve

    def _delete(self, error=None):
        def delete(customer_id):
            self.calls.append(("delete", customer_id))
            if error:
                raise error

        return delete


class ExpireOpenCheckouts(_StripeFakes):
    def test_expires_each_open_session(self):
        with patch.object(stripe.checkout.Session, "expire", self._expire()):
            service.expire_open_checkouts(["cs_a", "cs_b"])
        self.assertEqual(self.calls, [("expire", "cs_a"), ("expire", "cs_b")])

    def test_expired_or_unpaid_sessions_are_fine(self):
        # Expiring a session that isn't open is an InvalidRequestError; an
        # expired one, or an async payment still pending, doesn't block.
        for status, payment_status in (("expired", "unpaid"), ("complete", "unpaid")):
            with (
                self.subTest(status=status, payment_status=payment_status),
                patch.object(
                    stripe.checkout.Session,
                    "expire",
                    self._expire(_invalid_request(None)),
                ),
                patch.object(
                    stripe.checkout.Session,
                    "retrieve",
                    self._retrieve(status, payment_status),
                ),
            ):
                service.expire_open_checkouts(["cs_x"])

    def test_paid_but_uncredited_session_must_settle_first(self):
        with (
            patch.object(
                stripe.checkout.Session, "expire", self._expire(_invalid_request(None))
            ),
            patch.object(
                stripe.checkout.Session, "retrieve", self._retrieve("complete", "paid")
            ),
            self.assertRaises(service.CheckoutStillSettling),
        ):
            service.expire_open_checkouts(["cs_paid"])

    def test_unreachable_stripe_propagates(self):
        with (
            patch.object(
                stripe.checkout.Session,
                "expire",
                self._expire(stripe.APIConnectionError("down")),
            ),
            self.assertRaises(stripe.StripeError),
        ):
            service.expire_open_checkouts(["cs_open"])


class DeleteStripeCustomer(_StripeFakes):
    def test_deletes_the_customer(self):
        with patch.object(stripe.Customer, "delete", self._delete()):
            service.delete_stripe_customer("cus_1")
        self.assertEqual(self.calls, [("delete", "cus_1")])

    def test_already_deleted_customer_is_fine(self):
        with patch.object(
            stripe.Customer,
            "delete",
            self._delete(_invalid_request("resource_missing")),
        ):
            service.delete_stripe_customer("cus_1")

    def test_other_errors_propagate(self):
        for error in (
            _invalid_request("parameter_invalid"),
            stripe.APIConnectionError("down"),
        ):
            with (
                self.subTest(error=type(error).__name__),
                patch.object(stripe.Customer, "delete", self._delete(error)),
                self.assertRaises(stripe.StripeError),
            ):
                service.delete_stripe_customer("cus_1")


if __name__ == "__main__":
    unittest.main()
