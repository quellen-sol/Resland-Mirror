"""account.storage — the user's S3 prefix, paginated listing, batched deletes.

Run: .venv/bin/python -m unittest backend.api.tests.test_account_storage -v
"""

import unittest

from botocore.exceptions import ClientError

from api.account import storage

from .helpers import FakeS3

BUCKET = "b"


def _objects(user_id, n):
    return {f"resumes/{user_id}/tailored/{i:05}.docx": b"x" for i in range(n)}


class UserPrefix(unittest.TestCase):
    def test_trailing_slash(self):
        self.assertEqual(storage.user_prefix("auth0|abc"), "resumes/auth0|abc/")

    def test_rejects_ids_that_could_escape_the_prefix(self):
        for bad in ("", "a/b", "../x", "auth0|a/"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                storage.user_prefix(bad)


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


class DeletePrefix(unittest.TestCase):
    def test_deletes_every_object_in_batches(self):
        objects = _objects("u1", 2500)
        # A lookalike user whose id extends u1's must be untouched.
        objects.update(_objects("u10", 3))
        objects["resumes/u1/resume_doc.docx"] = b"r"
        s3 = FakeS3(objects, page_size=1000)

        deleted = storage.delete_prefix(s3, BUCKET, "resumes/u1/")

        self.assertEqual(deleted, 2501)
        self.assertEqual(sorted(s3.objects), sorted(_objects("u10", 3)))
        self.assertTrue(all(len(b) <= 1000 for b in s3.delete_calls))
        self.assertEqual(sum(len(b) for b in s3.delete_calls), 2501)

    def test_nothing_to_delete(self):
        s3 = FakeS3()
        self.assertEqual(storage.delete_prefix(s3, BUCKET, "resumes/u1/"), 0)
        self.assertEqual(s3.delete_calls, [])

    def test_per_key_errors_raise(self):
        # DeleteObjects reports per-key failures in a 200 response — they
        # must not pass for success.
        s3 = FakeS3(_objects("u1", 3))
        s3.fail_delete_keys = {"resumes/u1/tailored/00001.docx"}
        with self.assertRaises(storage.StorageError):
            storage.delete_prefix(s3, BUCKET, "resumes/u1/")


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

        s3 = FakeS3({f"{prefix}a.docx": b"x"})
        s3.fail_delete_keys = {f"{prefix}a.docx"}
        with self.assertRaises(storage.StorageError) as ctx:
            storage.delete_prefix(s3, BUCKET, prefix)
        self.assertNotIn("google-oauth2|42", str(ctx.exception))

        s3 = FakeS3({f"{prefix}a.docx": b"x"})
        s3.fail_get = denied
        with self.assertRaises(storage.StorageError) as ctx:
            storage.open_object(s3, BUCKET, f"{prefix}a.docx")
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
