"""account.storage — the user's S3 prefix and files, paginated listing,
batched deletes.

Run: .venv/bin/python -m unittest backend.api.tests.test_account_storage -v
"""

import unittest
import uuid

from botocore.exceptions import ClientError

from api.account import storage
from api.resume_export.service import GENERATED_KEY_TEMPLATE
from api.tailored.service import GENERATED_TAILORED_KEY_TEMPLATE

from .helpers import FakeS3

BUCKET = "b"


def tailored_key(user_id, i):
    return f"resumes/{user_id}/tailored/{uuid.UUID(int=i)}.docx"


def _objects(user_id, n):
    return {tailored_key(user_id, i): b"x" for i in range(n)}


class UserPrefix(unittest.TestCase):
    def test_trailing_slash(self):
        self.assertEqual(storage.user_prefix("auth0|abc"), "resumes/auth0|abc/")

    def test_ids_with_a_slash_get_the_prefix_uploads_use(self):
        # Uploads build resumes/<raw id>/…; export and deletion must look in
        # the same place rather than erroring.
        self.assertEqual(
            storage.user_prefix("samlp|corp/jane"), "resumes/samlp|corp/jane/"
        )

    def test_rejects_an_empty_id(self):
        with self.assertRaises(ValueError):
            storage.user_prefix("")


class UserFiles(unittest.TestCase):
    def test_every_writer_key_is_recognized(self):
        """Pins the key formats of the three writers: a new kind of file
        has to be added to USER_FILE, or export/deletion won't see it."""
        tid = str(uuid.uuid4())
        prefix = storage.user_prefix("auth0|u1")
        for key in (
            f"{prefix}resume_doc.docx",  # resume_upload.service, docx
            f"{prefix}resume_doc.pdf",  # resume_upload.service, pdf
            GENERATED_KEY_TEMPLATE.format(user_id="auth0|u1"),
            GENERATED_TAILORED_KEY_TEMPLATE.format(user_id="auth0|u1", tailored_id=tid),
        ):
            with self.subTest(key=key):
                self.assertTrue(storage.is_user_file(prefix, key))

    def test_other_accounts_sharing_the_prefix_are_not_ours(self):
        prefix = storage.user_prefix("a")
        for key in (
            "resumes/a/b/resume_doc.docx",  # account "a/b"
            "resumes/a/b/generated.docx",
            f"resumes/a/b/tailored/{uuid.uuid4()}.docx",
            # account "a/tailored": its upload looks like a tailored file
            # only to a matcher that doesn't insist on a uuid.
            "resumes/a/tailored/resume_doc.docx",
            "resumes/a/tailored/generated.docx",
            "resumes/a/notes.txt",
            "resumes/a/",
        ):
            with self.subTest(key=key):
                self.assertFalse(storage.is_user_file(prefix, key))

    def test_listing_keeps_each_account_to_its_own_files(self):
        objects = {
            "resumes/a/resume_doc.docx": b"a",
            "resumes/a/generated.docx": b"a",
            "resumes/a/b/resume_doc.pdf": b"ab",
            "resumes/a/b/generated.docx": b"ab",
            "resumes/a/stray.bin": b"?",
        }
        s3 = FakeS3(objects)
        self.assertEqual(
            sorted(storage.list_user_files(s3, BUCKET, storage.user_prefix("a"))),
            ["resumes/a/generated.docx", "resumes/a/resume_doc.docx"],
        )
        self.assertEqual(
            sorted(storage.list_user_files(s3, BUCKET, storage.user_prefix("a/b"))),
            ["resumes/a/b/generated.docx", "resumes/a/b/resume_doc.pdf"],
        )


class ListKeys(unittest.TestCase):
    def test_follows_pagination(self):
        s3 = FakeS3(_objects("u1", 2500), page_size=1000)
        keys = storage.list_keys(s3, BUCKET, "resumes/u1/")
        self.assertEqual(len(keys), 2500)
        self.assertEqual(len(s3.list_calls), 3)

    def test_empty_prefix(self):
        self.assertEqual(storage.list_keys(FakeS3(), BUCKET, "resumes/u1/"), [])

    def test_failure_raises_storage_error(self):
        s3 = FakeS3()
        s3.fail_list = ClientError({"Error": {"Code": "AccessDenied"}}, "List")
        with self.assertRaises(storage.StorageError):
            storage.list_keys(s3, BUCKET, "resumes/u1/")


class DeleteUserFiles(unittest.TestCase):
    def test_deletes_every_file_in_batches(self):
        objects = _objects("u1", 2500)
        # A lookalike user whose id extends u1's must be untouched.
        objects.update(_objects("u10", 3))
        objects["resumes/u1/resume_doc.docx"] = b"r"
        s3 = FakeS3(objects, page_size=1000)

        deleted = storage.delete_user_files(s3, BUCKET, "resumes/u1/")

        self.assertEqual(deleted, 2501)
        self.assertEqual(sorted(s3.objects), sorted(_objects("u10", 3)))
        self.assertTrue(all(len(b) <= 1000 for b in s3.delete_calls))
        self.assertEqual(sum(len(b) for b in s3.delete_calls), 2501)

    def test_another_accounts_files_under_the_prefix_survive(self):
        s3 = FakeS3(
            {
                "resumes/a/resume_doc.docx": b"a",
                "resumes/a/b/resume_doc.docx": b"ab",
            }
        )
        self.assertEqual(storage.delete_user_files(s3, BUCKET, "resumes/a/"), 1)
        self.assertEqual(list(s3.objects), ["resumes/a/b/resume_doc.docx"])

    def test_nothing_to_delete(self):
        s3 = FakeS3()
        self.assertEqual(storage.delete_user_files(s3, BUCKET, "resumes/u1/"), 0)
        self.assertEqual(s3.delete_calls, [])

    def test_per_key_errors_raise(self):
        # DeleteObjects reports per-key failures in a 200 response — they
        # must not pass for success.
        s3 = FakeS3(_objects("u1", 3))
        s3.fail_delete_keys = {tailored_key("u1", 1)}
        with self.assertRaises(storage.StorageError):
            storage.delete_user_files(s3, BUCKET, "resumes/u1/")


class ErrorsStayAnonymous(unittest.TestCase):
    """StorageError messages end up in logs that outlive a deleted account,
    so they must not carry the key or prefix (both contain the Auth0 id)."""

    def test_no_message_names_the_user(self):
        denied = ClientError({"Error": {"Code": "AccessDenied"}}, "Op")
        prefix = "resumes/google-oauth2|42/"

        s3 = FakeS3()
        s3.fail_list = denied
        with self.assertRaises(storage.StorageError) as ctx:
            storage.list_keys(s3, BUCKET, prefix)
        self.assertNotIn("google-oauth2|42", str(ctx.exception))

        s3 = FakeS3({f"{prefix}generated.docx": b"x"})
        s3.fail_delete_keys = {f"{prefix}generated.docx"}
        with self.assertRaises(storage.StorageError) as ctx:
            storage.delete_user_files(s3, BUCKET, prefix)
        self.assertNotIn("google-oauth2|42", str(ctx.exception))

        s3 = FakeS3({f"{prefix}generated.docx": b"x"})
        s3.fail_get = denied
        with self.assertRaises(storage.StorageError) as ctx:
            storage.open_object(s3, BUCKET, f"{prefix}generated.docx")
        self.assertNotIn("google-oauth2|42", str(ctx.exception))


class OpenObject(unittest.TestCase):
    def test_reads_body(self):
        s3 = FakeS3({"resumes/u1/a.docx": b"data"})
        body = storage.open_object(s3, BUCKET, "resumes/u1/a.docx")
        self.assertEqual(body.read(), b"data")

    def test_missing_is_none(self):
        self.assertIsNone(storage.open_object(FakeS3(), BUCKET, "resumes/u1/x"))

    def test_other_errors_raise(self):
        s3 = FakeS3({"resumes/u1/a.docx": b"data"})
        s3.fail_get = ClientError({"Error": {"Code": "AccessDenied"}}, "Get")
        with self.assertRaises(storage.StorageError):
            storage.open_object(s3, BUCKET, "resumes/u1/a.docx")


if __name__ == "__main__":
    unittest.main()
