"""The MCP server: Resland's profile, memory bank, and tailored-resume board as
tools, plus a tailor prompt. Claude does the writing on your own plan; the
server only reads and saves through the Resland API."""

import asyncio
import re
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from .api import ReslandApi
from .config import Settings
from .prompts import INSTRUCTIONS, TAILORING_GUIDE, tailor_prompt

PdfConverter = Callable[[Path], Awaitable[Path]]


class NewFact(BaseModel):
    topic: str = Field(
        description='"<title> at <company>" exactly as the profile shows the job, '
        'a project\'s name, "Preferences", or "General".'
    )
    content: str = Field(
        description="One self-contained fact, keeping the user's numbers and names."
    )
    replaces_id: int | None = Field(
        default=None,
        description="A memory fact's id this one corrects or extends; that fact "
        "is rewritten in place instead of adding a second one.",
    )


class TailoredExperience(BaseModel):
    experience_id: int = Field(description="An experience id from get_profile.")
    bullets: list[str] = Field(
        description="This job's tailored bullets, in display order."
    )


class EditedExperience(BaseModel):
    company_name: str
    title: str
    location: str | None = None
    start_date: str
    end_date: str | None = None
    bullets: list[str]


class EditedSkillGroup(BaseModel):
    category: str | None = None
    skills: list[str]


class EditedContent(BaseModel):
    summary: str | None = None
    experiences: list[EditedExperience]
    skill_groups: list[EditedSkillGroup]


# LibreOffice's first run builds a profile, so leave it room.
PDF_TIMEOUT_SECONDS = 120


async def libreoffice_to_pdf(docx: Path) -> Path:
    """Convert next to the docx with headless LibreOffice."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise ToolError(
            "PDF export needs LibreOffice (`soffice` on PATH). The DOCX is "
            f"saved at {docx}."
        )
    proc = await asyncio.create_subprocess_exec(
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(docx.parent),
        str(docx),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), PDF_TIMEOUT_SECONDS)
    except TimeoutError:
        proc.kill()
        raise ToolError(f"LibreOffice timed out converting {docx}.") from None
    pdf = docx.with_suffix(".pdf")
    if proc.returncode != 0 or not pdf.exists():
        raise ToolError(
            f"LibreOffice couldn't convert {docx}: {stderr.decode(errors='replace')[:300]}"
        )
    return pdf


def _slug(*parts: str | None) -> str:
    words = re.sub(r"[^a-z0-9]+", "-", " ".join(p for p in parts if p).lower())
    return words.strip("-")[:80].strip("-")


def create_server(
    api: ReslandApi, settings: Settings, *, to_pdf: PdfConverter = libreoffice_to_pdf
) -> MCPServer:
    server = MCPServer("resland", instructions=INSTRUCTIONS)

    def link(tailored_id: str) -> str:
        return f"{settings.app_url}/tailored/{tailored_id}"

    @server.tool()
    async def get_tailoring_guide() -> str:
        """Resland's rules for tailoring a resume to a job posting: the
        workflow (interview the user before writing), how to rewrite bullets
        honestly, and how to use the memory bank. Call it before tailoring
        a resume or rewriting bullets, and follow it."""
        return TAILORING_GUIDE

    @server.tool()
    async def get_profile() -> dict[str, Any]:
        """The user's Resland base profile: header, social links, experiences
        (newest first, each with its id and its bullets' ids in display order),
        skills in display order with their categories, education, projects."""
        return await api.get_profile()

    @server.tool()
    async def list_memory() -> dict[str, Any]:
        """The user's memory bank: facts they told earlier sessions about
        their work and preferences, grouped by topic. Treat them like answers
        the user just gave."""
        return await api.list_memory()

    @server.tool()
    async def remember_facts(facts: list[NewFact]) -> dict[str, Any]:
        """Save lasting facts the user told you about their work, or their
        preferences, to their memory bank so later sessions (here and on the
        site) don't ask again."""
        return await api.remember([fact.model_dump() for fact in facts])

    @server.tool()
    async def list_tailored_resumes() -> dict[str, Any]:
        """The tailored resumes on the user's Resland board, newest first."""
        listed = await api.list_tailored()
        for item in listed.get("items", []):
            item["url"] = link(item["id"])
        return listed

    @server.tool()
    async def get_tailored_resume(tailored_id: str) -> dict[str, Any]:
        """One tailored resume: its job posting and its full content."""
        tailored = await api.get_tailored(tailored_id)
        return {**tailored, "url": link(tailored["id"])}

    @server.tool()
    async def save_tailored_resume(
        job_description: Annotated[str, Field(description="The full job posting.")],
        experiences: Annotated[
            list[TailoredExperience],
            Field(
                description="Every experience from the profile, in the profile's order."
            ),
        ],
        skills: Annotated[
            list[str],
            Field(description="The profile's skill names, reordered by relevance."),
        ],
        company_name: str | None = None,
        role: str | None = None,
        summary: Annotated[
            str | None, Field(description="Only when the user wants a summary.")
        ] = None,
    ) -> dict[str, Any]:
        """Save a tailored resume to the user's Resland board. Company, titles
        and dates come from the profile through the experience ids; skills are
        grouped by their profile category. Returns its id and a link."""
        created = await api.create_tailored(
            {
                "job_description": job_description,
                "company_name": company_name,
                "role": role,
                "summary": summary,
                "experiences": [e.model_dump() for e in experiences],
                "skills": skills,
            }
        )
        return {"id": created["id"], "url": link(created["id"])}

    @server.tool()
    async def update_tailored_resume(
        tailored_id: str,
        content: Annotated[
            EditedContent | None,
            Field(description="The full content from get_tailored_resume, edited."),
        ] = None,
        company_name: str | None = None,
        role: str | None = None,
        job_description: str | None = None,
    ) -> dict[str, Any]:
        """Revise a saved tailored resume. Only the fields you pass change."""
        changes: dict[str, Any] = {}
        if content is not None:
            changes["content"] = content.model_dump()
        for field, value in (
            ("company_name", company_name),
            ("role", role),
            ("job_description", job_description),
        ):
            if value is not None:
                changes[field] = value
        if not changes:
            raise ToolError("Nothing to update: pass content or a field to change.")
        updated = await api.update_tailored(tailored_id, changes)
        return {**updated, "url": link(updated["id"])}

    @server.tool()
    async def export_tailored_resume(
        tailored_id: str,
        format: Literal["docx", "pdf"] = "docx",
        directory: Annotated[
            str | None,
            Field(description="Where to save it; defaults to RESLAND_EXPORT_DIR."),
        ] = None,
    ) -> dict[str, Any]:
        """Render a tailored resume in the layout of the user's uploaded
        resume and save it as a local file. Returns the file's path."""
        exported = await api.export_tailored(tailored_id)
        tailored = await api.get_tailored(tailored_id)
        out_dir = Path(directory).expanduser() if directory else settings.export_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        name = _slug(
            tailored.get("company_name"), tailored.get("role"), tailored_id[:8]
        )
        docx = out_dir / f"{name}.docx"
        docx.write_bytes(await api.download(exported["url"]))
        path = await to_pdf(docx) if format == "pdf" else docx
        return {"path": str(path), "regenerated": exported.get("regenerated", False)}

    @server.prompt()
    def tailor(
        job_description: str = "", company_name: str = "", role: str = ""
    ) -> str:
        """Tailor your Resland resume to a job posting: interview, write, save."""
        return tailor_prompt(job_description, company_name, role)

    return server
