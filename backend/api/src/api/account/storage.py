"""S3 access for a user's files: everything under `resumes/<auth0_id>/`
(the original upload(s), generated.docx, tailored/<id>.docx).

Blocking boto3 calls — callers run these in a worker thread.
"""

from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

# S3 caps DeleteObjects at 1,000 keys per request.
DELETE_BATCH_SIZE = 1000

_MISSING_CODES = {"NoSuchKey", "404", "NotFound"}


class StorageError(Exception):
    """S3 refused a list/read/delete — the operation didn't complete."""


def user_prefix(user_id: str) -> str:
    """`resumes/<user_id>/` — the trailing slash keeps `auth0|ab` from
    matching `auth0|abc`'s files. Rejects ids that could escape the prefix."""
    if not user_id or "/" in user_id or user_id in (".", ".."):
        raise ValueError(f"unsafe user id for an S3 prefix: {user_id!r}")
    return f"resumes/{user_id}/"


def list_keys(s3: Any, bucket: str, prefix: str) -> list[str]:
    """Every key under `prefix`, following list_objects_v2 pagination."""
    keys: list[str] = []
    token: str | None = None
    try:
        while True:
            kwargs = {"Bucket": bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            page = s3.list_objects_v2(**kwargs)
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
            if not page.get("IsTruncated"):
                return keys
            token = page["NextContinuationToken"]
    except (BotoCoreError, ClientError) as e:
        raise StorageError(f"listing {prefix}: {e}") from e


def delete_prefix(s3: Any, bucket: str, prefix: str) -> int:
    """Delete every object under `prefix` in DeleteObjects batches. Returns
    how many were deleted; raises StorageError if any key failed."""
    keys = list_keys(s3, bucket, prefix)
    for start in range(0, len(keys), DELETE_BATCH_SIZE):
        batch = keys[start : start + DELETE_BATCH_SIZE]
        try:
            resp = s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": k} for k in batch], "Quiet": True},
            )
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"deleting under {prefix}: {e}") from e
        # Per-key failures come back in a 200 response, not as an exception.
        errors = resp.get("Errors") or []
        if errors:
            first = errors[0]
            raise StorageError(
                f"{len(errors)} object(s) under {prefix} not deleted"
                f" (first: {first.get('Code')} {first.get('Message')})"
            )
    return len(keys)


def open_object(s3: Any, bucket: str, key: str) -> Any | None:
    """The object's streaming body, or None when it no longer exists (it can
    vanish between listing and reading). Other failures raise StorageError."""
    try:
        return s3.get_object(Bucket=bucket, Key=key)["Body"]
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in _MISSING_CODES:
            return None
        raise StorageError(f"reading {key}: {e}") from e
    except BotoCoreError as e:
        raise StorageError(f"reading {key}: {e}") from e
