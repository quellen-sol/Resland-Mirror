# TODO: README follow-ups (PR #78)

Working notes for the README on this branch. Delete this file before merging.

## README content

- [ ] **Add an author section.** The README doesn't name you. Add your name and how to
      reach you (LinkedIn, portfolio, an email you're happy to publish) at the bottom.
- [ ] **Confirm resland.org is open** before linking recruiters to it. Terraform seeds
      `MAINTENANCE_MODE=1` (`terraform/api.tf`), so a fresh deploy starts in maintenance
      mode until it's turned off in `/admin`.
- [ ] **Mention where the frontend is hosted.** The Infrastructure section only covers AWS.
      The frontend deploys on Vercel (the Vercel bot posts preview deploys on PRs).
- [ ] **Fix the PDF fixture wording in Tests.** It says the parser is tested against
      "real resumes". Since #80 the PDF fixtures keep real-world layouts (a Canva export,
      a Google Docs export) but their text is a fictional persona. Say "real-world resume
      layouts" instead.

## Before making the repo public

The repo is private right now. If recruiters will get a link to it:

- [ ] **`deploy.sh` hard-codes the AWS account ID.** Read it from an env var or
      `aws sts get-caller-identity`.
- [ ] **The production database and broker are reachable from the internet.**
      `terraform/rds.tf` has `publicly_accessible = true` with 5432 open to `0.0.0.0/0`,
      and `terraform/mq.tf` has `publicly_accessible = true`. Restrict them to the ECS
      services' security group (and your own IP for admin access).
- [ ] **`backend/shared/tests/fixtures/marquelle_original.docx` is your own resume.** #80
      replaced the third-party fixtures but kept this one. Check you're fine publishing
      the contact details in it, or swap them out the same way #80 did.

## Repo polish

- [ ] **Replace `frontend/README.md`.** It's still the create-next-app boilerplate. Point
      it at the root README instead.
- [ ] **Fill in the package metadata.** `backend/*/README.md` are empty, and each
      `pyproject.toml` still says `description = "Add your description here"`.
- [ ] **Rebase onto `master` if GitHub asks.** This branch is behind `master` by #80. The
      PR only adds files, so there should be no conflicts.
