import boto3


def get_s3_client(
    aws_access_key_id: str | None = None, aws_secret_access_key: str | None = None
):
    kwargs = {}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    return boto3.client("s3", **kwargs)
