import asyncio
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient

from .env_vars import AUTH0_AUDIENCE, AUTH0_DOMAIN

_jwks = PyJWKClient(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")


def _verify_token(token: str) -> str:
    key = _jwks.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        key.key,
        algorithms=["RS256"],
        audience=AUTH0_AUDIENCE,
        issuer=f"https://{AUTH0_DOMAIN}/",
    )
    return claims["sub"]


async def require_auth0_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        # JWKS fetch is blocking I/O — keep it off the event loop
        return await asyncio.to_thread(_verify_token, authorization[7:])
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid access token") from e


# Annotated alias so routes can declare `user_id: Auth0UserId` — FastAPI
# resolves the dependency and injects the token's `sub` as the argument. Neat!
Auth0UserId = Annotated[str, Depends(require_auth0_id)]
