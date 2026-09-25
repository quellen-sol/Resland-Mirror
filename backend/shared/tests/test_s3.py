"""get_s3_client tests — stdlib unittest, never touches AWS.

Run: .venv/bin/python -m unittest backend.shared.tests.test_s3 -v
"""

import unittest
from unittest.mock import patch

from shared.s3 import get_s3_client


class GetS3Client(unittest.TestCase):
    def _call_kwargs(self, **kwargs):
        with patch("shared.s3.boto3.client") as client:
            get_s3_client(**kwargs)
        return client.call_args

    def test_no_credentials_means_default_chain(self):
        args, kwargs = self._call_kwargs()
        self.assertEqual(args, ("s3",))
        self.assertNotIn("aws_access_key_id", kwargs)
        self.assertNotIn("aws_secret_access_key", kwargs)

    def test_partial_credentials_means_default_chain(self):
        # Only one of the pair set → still falls back to the default chain.
        args, kwargs = self._call_kwargs(aws_access_key_id="AKID")
        self.assertEqual(args, ("s3",))
        self.assertNotIn("aws_access_key_id", kwargs)
        self.assertNotIn("aws_secret_access_key", kwargs)

    def test_credentials_forwarded(self):
        _, kwargs = self._call_kwargs(
            aws_access_key_id="AKID", aws_secret_access_key="secret"
        )
        self.assertEqual(kwargs["aws_access_key_id"], "AKID")
        self.assertEqual(kwargs["aws_secret_access_key"], "secret")

    def test_signature_version_pinned_to_s3v4(self):
        # SigV2 presigned URLs are rejected by SigV4-only buckets.
        _, kwargs = self._call_kwargs()
        self.assertEqual(kwargs["config"].signature_version, "s3v4")

    def test_presigned_url_uses_sigv4(self):
        # Regression for the export error — presigning is offline, fake creds.
        s3 = get_s3_client(
            aws_access_key_id="AKID", aws_secret_access_key="secret"
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "b", "Key": "k"},
            ExpiresIn=60,
        )
        self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)


if __name__ == "__main__":
    unittest.main()
