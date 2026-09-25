"""get_s3_client tests — stdlib unittest, never touches AWS.

Run: .venv/bin/python -m unittest backend.shared.tests.test_s3 -v
"""

import os
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

    def test_region_name_forwarded(self):
        _, kwargs = self._call_kwargs(region_name="eu-west-1")
        self.assertEqual(kwargs["region_name"], "eu-west-1")

    def test_aws_region_env_used(self):
        # boto3 ignores AWS_REGION — get_s3_client resolves it so presigned
        # URLs aren't signed for us-east-1 by accident.
        with patch.dict(os.environ, {"AWS_REGION": "eu-west-1"}):
            os.environ.pop("AWS_DEFAULT_REGION", None)
            _, kwargs = self._call_kwargs()
        self.assertEqual(kwargs["region_name"], "eu-west-1")

    def test_aws_default_region_env_used(self):
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "ap-south-1"}):
            os.environ.pop("AWS_REGION", None)
            _, kwargs = self._call_kwargs()
        self.assertEqual(kwargs["region_name"], "ap-south-1")

    def test_explicit_region_beats_env(self):
        with patch.dict(os.environ, {"AWS_REGION": "eu-west-1"}):
            _, kwargs = self._call_kwargs(region_name="ap-south-1")
        self.assertEqual(kwargs["region_name"], "ap-south-1")

    def test_no_region_configured_omits_region_name(self):
        # Nothing configured → boto3's own chain (config file etc.) decides.
        with patch.dict(os.environ, {}):
            os.environ.pop("AWS_REGION", None)
            os.environ.pop("AWS_DEFAULT_REGION", None)
            _, kwargs = self._call_kwargs()
        self.assertNotIn("region_name", kwargs)

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

    def test_presigned_url_signed_for_aws_region(self):
        # Regression: AWS_REGION must reach the signer — a us-east-1-signed
        # URL is rejected by the us-east-2 bucket.
        with patch.dict(os.environ, {"AWS_REGION": "us-east-2"}):
            os.environ.pop("AWS_DEFAULT_REGION", None)
            s3 = get_s3_client(
                aws_access_key_id="AKID", aws_secret_access_key="secret"
            )
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": "b", "Key": "k"},
                ExpiresIn=60,
            )
        self.assertIn("us-east-2", url)


if __name__ == "__main__":
    unittest.main()
