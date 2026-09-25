"""get_s3_client tests — stdlib unittest, never touches AWS.

Run: .venv/bin/python -m unittest backend.shared.tests.test_s3 -v
"""

import unittest
from unittest.mock import patch

from shared.s3 import get_s3_client


class GetS3Client(unittest.TestCase):
    def test_no_credentials_means_default_chain(self):
        with patch("shared.s3.boto3.client") as client:
            get_s3_client()
        client.assert_called_once_with("s3")

    def test_partial_credentials_means_default_chain(self):
        # Only one of the pair set → still falls back to the default chain.
        with patch("shared.s3.boto3.client") as client:
            get_s3_client(aws_access_key_id="AKID")
        client.assert_called_once_with("s3")

    def test_credentials_forwarded(self):
        with patch("shared.s3.boto3.client") as client:
            get_s3_client(
                aws_access_key_id="AKID", aws_secret_access_key="secret"
            )
        client.assert_called_once_with(
            "s3", aws_access_key_id="AKID", aws_secret_access_key="secret"
        )


if __name__ == "__main__":
    unittest.main()
