"""The export archive: data.json, the user's files, and a README.

Layout:
    data.json            every row the user owns (see model.EXPORT_SECTIONS)
    files/<path>         objects under resumes/<auth0_id>/, path kept
    README.txt           what each part is and what isn't included
"""

import json
import textwrap
import zipfile
from typing import IO, Any

from . import storage

DATA_NAME = "data.json"
README_NAME = "README.txt"
FILES_DIR = "files/"
# Copy S3 bodies into the zip in chunks — resumes can be up to 100 MB.
CHUNK_SIZE = 1024 * 1024

_README_HEAD = """\
Your Resland data
=================

This archive holds a copy of everything Resland stores about your account.

data.json
---------
Your data as JSON. Dates are UTC (ISO 8601); money is in US cents.

  account          Your account id (from your sign-in provider), when the
                   account was created, your balance, and your Stripe
                   customer reference.
  login_identity   Your sign-in profile as our sign-in provider, Auth0,
                   holds it: email, name, picture, and recent sign-in
                   details.
  profile, links, experiences (each with its bullets), skills, education,
  projects         Your resume profile.
  resume_format    The layout captured from the resume you uploaded.
  generated_resume, resume_uploads
                   When your resume was last generated and uploaded.
  suggestions      Bullet suggestions, including the questions the AI asked
                   and the options it wrote.
  tailor_runs, tailored_resumes
                   Tailoring runs and your saved tailored resumes, including
                   the job descriptions you pasted.
  system_design_sessions
                   Your mock interviews: notes, estimates, diagram, the full
                   transcript (messages), and the graded report.
  dsa_progress     DSA Study Center topics you marked as studied.
  memory           Facts about your work that tailoring and suggestions
                   saved from your answers, or that you added on /memory.
  purchases        Your balance purchases.
  usage            Each AI action you were charged for, and what it cost.

files/
------
The files stored for your account:

  resume_doc.docx / resume_doc.pdf   The resume you last uploaded (one per
                                     file type).
  generated.docx                     The last resume you exported.
  tailored/<id>.docx                 Exported tailored resumes; <id> matches
                                     tailored_resumes in data.json.

"""

_README_EXCLUDED = """
Not included
------------
- The AI assistant's working state. While a suggestion or tailoring session
  is open, the assistant keeps its own internal notes on the conversation
  (including your answers to its questions and any guidance you typed) so it
  can pick up where it left off. They aren't stored in a readable form, and
  they're deleted when the session is accepted, dismissed or replaced, or
  when you delete your account. Mock interview transcripts are included in
  full above.
- Internal bookkeeping: storage paths and cache keys, the interviewer's
  hidden notes for each mock interview, our own provider costs and request
  ids, and admin flags.
- Card and payment details. Payments go through Stripe, which keeps those
  records; Resland never sees your card.
- Short-lived server logs.
"""

# Why login_identity is empty, when it is — the service picks one.
IDENTITY_UNAVAILABLE = (
    "Your sign-in profile (login_identity) couldn't be retrieved from Auth0 "
    "for this export, so it's empty. Try exporting again later to include it."
)
IDENTITY_NOT_FOUND = (
    "Auth0 holds no sign-in profile for this account, so login_identity is empty."
)
IDENTITY_NOT_FETCHED = (
    "Your sign-in profile (login_identity) isn't included in this export."
)


def readme_text(*, files: list[str], login_identity_note: str | None) -> str:
    """README.txt for one archive: lists the files actually included and says
    plainly what isn't (agent working state, Stripe's records, logs).
    `login_identity_note` explains an empty login_identity; None when it's
    there."""
    if files:
        listing = "Included in this export:\n" + "".join(
            f"  {name}\n" for name in files
        )
    else:
        listing = "No files are stored for your account.\n"
    text = _README_HEAD + listing + _README_EXCLUDED
    if login_identity_note:
        text += "\n" + textwrap.fill(f"Note: {login_identity_note}", 76) + "\n"
    return text


def write_archive(
    dest: IO[bytes],
    *,
    data: dict[str, Any],
    s3: Any,
    bucket: str,
    prefix: str,
    keys: list[str],
    login_identity_note: str | None,
) -> list[str]:
    """Write the zip into `dest`. Each key under `prefix` lands at
    files/<key minus prefix>; a key that vanished since listing is skipped.
    Returns the archive names of the files included. Blocking — run it in a
    worker thread."""
    included: list[str] = []
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(DATA_NAME, json.dumps(data, indent=2, ensure_ascii=False))
        for key in keys:
            if not key.startswith(prefix) or key == prefix:
                continue
            body = storage.open_object(s3, bucket, key)
            if body is None:
                continue
            name = FILES_DIR + key[len(prefix) :]
            try:
                with zf.open(name, "w", force_zip64=True) as out:
                    while chunk := body.read(CHUNK_SIZE):
                        out.write(chunk)
            finally:
                body.close()
            included.append(name)
        zf.writestr(
            README_NAME,
            readme_text(files=included, login_identity_note=login_identity_note),
        )
    return included
