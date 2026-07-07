"""Minimal OIDC provider support.

This implements just enough of the OpenID Connect authorization code flow to
act as an identity provider for first-party services such as Outline. Relying
parties are configured statically (see OIDC_CLIENT_* config), authorization
codes are stored in redis with a short TTL, and access tokens reuse the
regular access_tokens table so the existing bearer authentication applies to
the userinfo endpoint.

Note that no signed id_token is issued: clients are expected to fetch claims
from the userinfo endpoint using the access token.
"""

import hmac
import json
import secrets
from dataclasses import dataclass
from logging import getLogger
from typing import Optional
from urllib.parse import urlencode

from redis_cache import redis_connection
from service import config

logger = getLogger("makeradmin")

# How long an authorization code stays valid. The client exchanges it
# immediately after the redirect, so this can be short.
AUTHORIZATION_CODE_TTL_SECONDS = 60

# How long the access token issued to the client stays valid. It is only used
# to query the userinfo endpoint right after login.
ACCESS_TOKEN_TTL_SECONDS = 600

REDIS_KEY_PREFIX = "oidc:authorization_code:"


@dataclass(frozen=True)
class OIDCClient:
    client_id: str
    client_secret: str
    redirect_uris: list[str]


def get_configured_client() -> Optional[OIDCClient]:
    client_id = config.config.get("OIDC_CLIENT_ID")
    client_secret = config.config.get("OIDC_CLIENT_SECRET")
    redirect_uris = config.config.get("OIDC_REDIRECT_URIS")
    if not client_id or not client_secret or not redirect_uris:
        return None
    return OIDCClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uris=[uri.strip() for uri in redirect_uris.split(",") if uri.strip()],
    )


def validate_client_id(client_id: str) -> Optional[OIDCClient]:
    client = get_configured_client()
    if client is None:
        logger.warning("OIDC login attempted but no OIDC client is configured")
        return None
    if not hmac.compare_digest(client.client_id, client_id):
        return None
    return client


def validate_client_credentials(client_id: str, client_secret: str) -> Optional[OIDCClient]:
    client = validate_client_id(client_id)
    if client is None:
        return None
    if not hmac.compare_digest(client.client_secret, client_secret):
        return None
    return client


def issue_authorization_code(member_id: int, client: OIDCClient, redirect_uri: str, state: Optional[str]) -> str:
    """Issue a single-use authorization code and return the URL to redirect the browser to."""
    code = secrets.token_urlsafe(32)
    payload = json.dumps(dict(member_id=member_id, client_id=client.client_id, redirect_uri=redirect_uri))
    redis_connection.set(REDIS_KEY_PREFIX + code, payload, ex=AUTHORIZATION_CODE_TTL_SECONDS)

    params = dict(code=code)
    if state is not None:
        params["state"] = state
    separator = "&" if "?" in redirect_uri else "?"
    return f"{redirect_uri}{separator}{urlencode(params)}"


def redeem_authorization_code(code: str, client: OIDCClient, redirect_uri: Optional[str]) -> Optional[int]:
    """Redeem a single-use authorization code, returning the member_id it was issued for."""
    payload = redis_connection.getdel(REDIS_KEY_PREFIX + code)
    if payload is None:
        return None
    data = json.loads(payload)
    if data["client_id"] != client.client_id:
        return None
    # The OAuth2 spec requires the token request to repeat the redirect_uri
    # used in the authorization request, but some clients omit it.
    if redirect_uri is not None and data["redirect_uri"] != redirect_uri:
        return None
    return int(data["member_id"])
