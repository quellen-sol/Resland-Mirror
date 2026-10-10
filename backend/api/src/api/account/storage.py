"""S3 access for a user's files under `resumes/<auth0_id>/`: the original
upload(s), generated.docx, tailored/<uuid>.docx.

A user's files are recognized by those exact key shapes, not just the prefix:
uploads build keys from the raw Auth0 id, so an id containing `/` (rare, but
Auth0 doesn't forbid it) shares its prefix with a shorter id —
`resumes/a/b/resume_doc.docx` sits under both `resumes/a/` and `resumes/a/b/`.
Matching the shapes keeps each account's export and deletion to its own files.

Blocking boto3 calls — callers run these in a worker thread.
"""

import re
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

# S3 caps DeleteObjects at 1,000 keys per request.
DELETE_BATCH_SIZE = 1000

_MISSING_CODES = {"NoSuchKey", "404", "NotFound"}


class StorageError(Exception):
    """S3 refused a list/read/delete — the operation didn't complete.

    Messages never name the key or prefix: both contain the Auth0 id, and
    these end up in logs that outlive a deleted account."""


# Every key the app writes under a user's prefix (resume_upload, the resume
# export and the tailored export). A new kind of file must be added here, or
# export and deletion won't see it — tests pin the writers' key formats.
USER_FILE = re.compile(
    r"(resume_doc\.(docx|pdf)"
    r"|generated\.docx"
    r"|tailored/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.docx)"
)


def user_prefix(user_id: str) -> str:
    """`resumes/<user_id>/`, the same prefix uploads write under. The
    trailing slash keeps `auth0|ab` from matching `auth0|abc`'s files."""
    if not user_id:
        raise ValueError("empty user id")
    return f"resumes/{user_id}/"


def is_user_file(prefix: str, key: str) -> bool:
    """Whether `key` is one of the files the app writes for the user whose
    prefix this is (and not another account's file sharing the prefix)."""
    return (
        key.startswith(prefix) and USER_FILE.fullmatch(key[len(prefix) :]) is not None
    )


def list_user_files(s3: Any, bucket: str, prefix: str) -> list[str]:
    """The user's files under `prefix` (see USER_FILE). Anything else found
    there is left alone, and logged by count so it isn't silent."""
    keys = list_keys(s3, bucket, prefix)
    mine = [k for k in keys if is_user_file(prefix, k)]
    if len(mine) != len(keys):
        # No key or prefix in the message: both carry an Auth0 id.
        print(f"{len(keys) - len(mine)} object(s) under a user prefix aren't theirs")
    return mine


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
        raise StorageError(f"listing failed: {e}") from e


def delete_user_files(s3: Any, bucket: str, prefix: str) -> int:
    """Delete the user's files under `prefix` in DeleteObjects batches.
    Returns how many were deleted; raises StorageError if any key failed."""
    keys = list_user_files(s3, bucket, prefix)
    for start in range(0, len(keys), DELETE_BATCH_SIZE):
        batch = keys[start : start + DELETE_BATCH_SIZE]
        try:
            resp = s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": k} for k in batch], "Quiet": True},
            )
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"delete failed: {e}") from e
        # Per-key failures come back in a 200 response, not as an exception.
        errors = resp.get("Errors") or []
        if errors:
            first = errors[0]
            raise StorageError(
                f"{len(errors)} object(s) not deleted"
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
        raise StorageError(f"read failed: {e}") from e
    except BotoCoreError as e:
        raise StorageError(f"read failed: {e}") from e
