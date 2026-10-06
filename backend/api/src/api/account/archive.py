"""The export archive: data.json, the user's files, and a README.

Layout:
    data.json            every row the user owns (see model.EXPORT_SECTIONS)
    files/<path>         objects under resumes/<auth0_id>/, path kept
    README.txt           what each part is and what isn't included
"""

from typing import IO, Any

DATA_NAME = "data.json"
README_NAME = "README.txt"
FILES_DIR = "files/"
# Copy S3 bodies into the zip in chunks — resumes can be up to 100 MB.
CHUNK_SIZE = 1024 * 1024


def readme_text(*, files: list[str], login_identity_included: bool) -> str:
    """README.txt for one archive: lists the files actually included and says
    plainly what isn't (agent working state, Stripe's records, logs)."""
    raise NotImplementedError


def write_archive(
    dest: IO[bytes],
    *,
    data: dict[str, Any],
    s3: Any,
    bucket: str,
    prefix: str,
    keys: list[str],
    login_identity_included: bool,
) -> list[str]:
    """Write the zip into `dest`. Each key under `prefix` lands at
    files/<key minus prefix>; a key that vanished since listing is skipped.
    Returns the archive names of the files included. Blocking — run it in a
    worker thread."""
    raise NotImplementedError
