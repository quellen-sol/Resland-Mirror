"""S3 access for a user's files: everything under `resumes/<auth0_id>/`
(the original upload(s), generated.docx, tailored/<id>.docx).

Blocking boto3 calls — callers run these in a worker thread.
"""

from typing import Any

# S3 caps DeleteObjects at 1,000 keys per request.
DELETE_BATCH_SIZE = 1000


class StorageError(Exception):
    """S3 refused a list/read/delete — the operation didn't complete."""


def user_prefix(user_id: str) -> str:
    """`resumes/<user_id>/` — the trailing slash keeps `auth0|ab` from
    matching `auth0|abc`'s files. Rejects ids that could escape the prefix."""
    raise NotImplementedError


def list_keys(s3: Any, bucket: str, prefix: str) -> list[str]:
    """Every key under `prefix`, following list_objects_v2 pagination."""
    raise NotImplementedError


def delete_prefix(s3: Any, bucket: str, prefix: str) -> int:
    """Delete every object under `prefix` in DeleteObjects batches. Returns
    how many were deleted; raises StorageError if any key failed."""
    raise NotImplementedError


def open_object(s3: Any, bucket: str, key: str) -> Any | None:
    """The object's streaming body, or None when it no longer exists (it can
    vanish between listing and reading). Other failures raise StorageError."""
    raise NotImplementedError
