"""Fakes for the MCP server tests: settings pointed at a tmp dir, and an
httpx2 transport that answers from per-route handlers and records requests."""

import json
from pathlib import Path
from urllib.parse import parse_qsl

import httpx2
from resland_mcp.config import Settings


def settings(tmp: Path) -> Settings:
    return Settings(
        api_url="https://api.test",
        app_url="https://app.test",
        auth0_domain="tenant.auth0.test",
        auth0_client_id="cli-123",
        auth0_audience="https://api.test/",
        credentials_path=tmp / "creds" / "credentials.json",
        export_dir=tmp / "exports",
    )


class FakeHttp:
    """routes: {(METHOD, url-without-query): handler(request) -> Response or
    a list of Responses served in order}."""

    def __init__(self, routes):
        self.routes = routes
        self.requests: list[httpx2.Request] = []

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        key = (request.method, str(request.url.copy_with(query=None)))
        route = self.routes.get(key)
        if route is None:
            return httpx2.Response(404, json={"detail": f"no fake for {key}"})
        if isinstance(route, list):
            return route.pop(0)
        return route(request)

    def client(self) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(transport=httpx2.MockTransport(self.handle))

    def sent(self, method: str, url: str) -> list[httpx2.Request]:
        return [
            r
            for r in self.requests
            if r.method == method and str(r.url.copy_with(query=None)) == url
        ]


def form(request: httpx2.Request) -> dict[str, str]:
    return dict(parse_qsl(request.content.decode()))


def body(request: httpx2.Request):
    return json.loads(request.content)
