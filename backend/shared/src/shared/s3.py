import os

import boto3
from botocore.config import Config

# SigV4 is mandatory for presigned URLs — without an explicit signature version
# the global endpoint falls back to SigV2, which SigV4-only buckets reject.
_S3_CONFIG = Config(signature_version="s3v4")


def get_s3_client(
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    region_name: str | None = None,
):
    # boto3 doesn't read AWS_REGION (only AWS_DEFAULT_REGION and ~/.aws/config)
    # — resolve it explicitly or presigned URLs get signed for the wrong region.
    region = (
        region_name
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )
    kwargs = {"config": _S3_CONFIG}
    if region:
        kwargs["region_name"] = region
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    return boto3.client("s3", **kwargs)
