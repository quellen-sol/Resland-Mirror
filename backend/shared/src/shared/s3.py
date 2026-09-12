import boto3


def get_s3_client(aws_access_key_id: str, aws_secret_access_key: str):
    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
