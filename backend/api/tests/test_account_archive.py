"""account.archive + the service's pure pieces (filename, Stripe step).

Run: .venv/bin/python -m unittest backend.api.tests.test_account_archive -v
"""

import datetime
import io
import json
import unittest
import zipfile
from unittest.mock import patch

import stripe

from api.account import archive, service

from .helpers import FakeS3

PREFIX = "resumes/u1/"


def _write(data=None, objects=None, keys=None, identity=True):
    s3 = FakeS3(objects or {})
    dest = io.BytesIO()
    included = archive.write_archive(
        dest,
        data=data or {"format_version": 1, "profile": {"full_name": "Jane"}},
        s3=s3,
        bucket="b",
        prefix=PREFIX,
        keys=keys if keys is not None else sorted(s3.objects),
        login_identity_included=identity,
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

    def test_readme_flags_a_missing_login_identity(self):
        with_identity = archive.readme_text(files=[], login_identity_included=True)
        without = archive.readme_text(files=[], login_identity_included=False)
        self.assertNotIn("couldn't be retrieved", with_identity)
        self.assertIn("couldn't be retrieved", without)


class ExportFilename(unittest.TestCase):
    def test_dated(self):
        self.assertEqual(
            service.export_filename(datetime.date(2026, 10, 6)),
            "resland-data-2026-10-06.zip",
        )


def _invalid_request(code):
    return stripe.InvalidRequestError("nope", None, code=code)


class DeleteStripeCustomer(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def _expire(self, error=None):
        def expire(session_id):
            self.calls.append(("expire", session_id))
            if error:
                raise error

        return expire

    def _delete(self, error=None):
        def delete(customer_id):
            self.calls.append(("delete", customer_id))
            if error:
                raise error

        return delete

    def test_expires_open_checkouts_then_deletes_the_customer(self):
        with (
            patch.object(stripe.checkout.Session, "expire", self._expire()),
            patch.object(stripe.Customer, "delete", self._delete()),
        ):
            service.delete_stripe_customer("cus_1", ["cs_a", "cs_b"])
        self.assertEqual(
            self.calls,
            [("expire", "cs_a"), ("expire", "cs_b"), ("delete", "cus_1")],
        )

    def test_already_finished_checkout_is_fine(self):
        # Expiring a completed/expired session is an InvalidRequestError.
        with (
            patch.object(
                stripe.checkout.Session,
                "expire",
                self._expire(_invalid_request(None)),
            ),
            patch.object(stripe.Customer, "delete", self._delete()),
        ):
            service.delete_stripe_customer("cus_1", ["cs_done"])
        self.assertIn(("delete", "cus_1"), self.calls)

    def test_already_deleted_customer_is_fine(self):
        with patch.object(
            stripe.Customer,
            "delete",
            self._delete(_invalid_request("resource_missing")),
        ):
            service.delete_stripe_customer("cus_1", [])

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
                service.delete_stripe_customer("cus_1", [])

    def test_unreachable_stripe_while_expiring_propagates(self):
        with (
            patch.object(
                stripe.checkout.Session,
                "expire",
                self._expire(stripe.APIConnectionError("down")),
            ),
            patch.object(stripe.Customer, "delete", self._delete()),
            self.assertRaises(stripe.StripeError),
        ):
            service.delete_stripe_customer("cus_1", ["cs_open"])
        # Never delete the customer while a checkout might still be payable.
        self.assertNotIn(("delete", "cus_1"), self.calls)


if __name__ == "__main__":
    unittest.main()
