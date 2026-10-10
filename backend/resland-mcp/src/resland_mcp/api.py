"""A thin client for the Resland API, signed in as you."""

from typing import Any
from urllib.parse import quote

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from .auth import LOGIN_HINT, NotLoggedIn, TokenProvider

# Generous: an export may render a docx server-side before it answers.
TIMEOUT_SECONDS = 60.0


class ApiError(ToolError):
    """The API refused or failed a request; the message is its own detail."""

    def __init__(self, status: int, detail: str):
        super().__init__(f"Resland API error {status}: {detail}")
        self.status = status
        self.detail = detail


class ReslandUnreachable(ToolError):
    pass


class ReslandApi:
    def __init__(self, base_url: str, tokens: TokenProvider, http: httpx2.AsyncClient):
        self.base_url = base_url
        self.tokens = tokens
        self.http = http

    async def _request(self, method: str, path: str, json: Any = None) -> Any:
        token = await self.tokens.token()
        try:
            resp = await self.http.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                headers={"Authorization": f"Bearer {token}"},
                timeout=TIMEOUT_SECONDS,
            )
        except httpx2.RequestError as e:
            raise ReslandUnreachable(
                f"Couldn't reach the Resland API at {self.base_url}: {e}"
            ) from e
        if resp.status_code == 401:
            raise NotLoggedIn(f"Resland didn't accept your login. {LOGIN_HINT}")
        if resp.is_error:
            raise ApiError(resp.status_code, _detail(resp))
        return resp.json()

    async def get_profile(self) -> dict[str, Any]:
        return await self._request("GET", "/profile")

    async def list_memory(self) -> dict[str, Any]:
        return await self._request("GET", "/memory")

    async def remember(self, facts: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._request("POST", "/memory", {"facts": facts})

    async def list_tailored(self) -> dict[str, Any]:
        return await self._request("GET", "/tailored")

    async def get_tailored(self, tailored_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/tailored/{_segment(tailored_id)}")

    async def create_tailored(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/tailored", body)

    async def update_tailored(
        self, tailored_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._request("PATCH", f"/tailored/{_segment(tailored_id)}", body)

    async def export_tailored(self, tailored_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/tailored/{_segment(tailored_id)}/export")

    async def download(self, url: str) -> bytes:
        """Fetch a presigned export URL, without the bearer token: it must
        never leave for S3."""
        try:
            resp = await self.http.get(url, timeout=TIMEOUT_SECONDS)
        except httpx2.RequestError as e:
            raise ReslandUnreachable(f"Couldn't download the export: {e}") from e
        if resp.is_error:
            raise ApiError(
                resp.status_code, f"export download failed: {resp.text[:200]}"
            )
        return resp.content


def _segment(value: str) -> str:
    """One path segment: an id can't climb to another route."""
    return quote(value, safe="")


def _detail(resp: httpx2.Response) -> str:
    """FastAPI's `detail`: a message, or a list of validation errors that
    each name the offending field."""
    try:
        detail = resp.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        problems = []
        for err in detail:
            loc = [str(part) for part in err.get("loc", []) if part != "body"]
            problems.append(
                f"{'.'.join(loc)}: {err.get('msg')}" if loc else str(err.get("msg"))
            )
        return "; ".join(problems)
    return resp.text[:500] or resp.reason_phrase
