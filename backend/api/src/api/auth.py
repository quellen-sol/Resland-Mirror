import asyncio
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request
from jwt import PyJWKClient
from psycopg import AsyncConnection
from psycopg.rows import TupleRow

from .account.db import token_revoked
from .deps import PgConnection
from .env_vars import AUTH0_AUDIENCE, AUTH0_DOMAIN, PG_URL

_jwks = PyJWKClient(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")


def _verify_claims(token: str) -> dict:
    key = _jwks.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        key.key,
        algorithms=["RS256"],
        audience=AUTH0_AUDIENCE,
        issuer=f"https://{AUTH0_DOMAIN}/",
    )


def _verify_token(token: str) -> str:
    return _verify_claims(token)["sub"]


async def require_auth0_id(
    pg_conn: PgConnection,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """The token's `sub`, once its signature checks out and it doesn't
    belong to a deleted account (see account.db.token_revoked). Shares the
    request's connection with the route."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        # JWKS fetch is blocking I/O — keep it off the event loop
        claims = await asyncio.to_thread(_verify_claims, authorization[7:])
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid access token") from e
    sub = claims["sub"]
    # A still-valid token from before the account was deleted (another
    # device, an open tab) must not keep working against a fresh account.
    if await token_revoked(pg_conn, sub, claims.get("iat")):
        raise HTTPException(status_code=401, detail="This account was deleted")
    return sub


# Annotated alias so routes can declare `user_id: Auth0UserId` — FastAPI
# resolves the dependency and injects the token's `sub` as the argument. Neat!
Auth0UserId = Annotated[str, Depends(require_auth0_id)]


async def _is_site_admin(pg_conn: AsyncConnection[TupleRow], user_id: str) -> bool:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT site_admin FROM "user" WHERE auth0_id = %s', (user_id,)
        )
        row = await res.fetchone()
    return bool(row and row[0])


async def is_site_admin_request(request: Request) -> bool:
    """Middleware-friendly admin check (no Depends): False on any failure."""
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        print("No bearer token")
        return False
    try:
        user_id = await asyncio.to_thread(_verify_token, authorization[7:])
        print(f"Got user_id: {user_id}")
        async with await AsyncConnection.connect(
            conninfo=PG_URL, autocommit=True
        ) as conn:
            site_admin = await _is_site_admin(conn, user_id)
            print(f"{user_id} Is site admin: {site_admin}")
            return site_admin
    except Exception as e:
        print(f"Exception from db: {e}")
        return False

def is_docs_request(request: Request) -> bool:
    # /docs alone isn't enough: Swagger UI and ReDoc fetch /openapi.json.
    path = request.url.path
    is_docs = path.startswith(("/docs", "/redoc")) or path == "/openapi.json"
    return is_docs


def is_stripe_webhook_request(request: Request) -> bool:
    """Stripe webhooks are unauthenticated machine calls — exempt like /docs
    so maintenance mode can't strand a paid checkout in PENDING."""
    return request.url.path == "/stripe/webhook"


async def require_site_admin(user_id: Auth0UserId, pg_conn: PgConnection) -> str:
    if not await _is_site_admin(pg_conn, user_id):
        # 403 not 401 — the request IS authenticated, it just isn't admin.
        raise HTTPException(status_code=403, detail="Not a site admin")
    return user_id


SiteAdmin = Annotated[str, Depends(require_site_admin)]
