"""Minimal OIDC provider support.

This implements just enough of the OpenID Connect authorization code flow to
act as an identity provider for first-party services such as Outline. Relying
parties are configured statically (see OIDC_CLIENTS config), authorization
codes are stored in redis with a short TTL, and access tokens reuse the
regular access_tokens table so the existing bearer authentication applies to
the userinfo endpoint.

Note that no signed id_token is issued: clients are expected to fetch claims
from the userinfo endpoint using the access token.

Client configuration:

    OIDC_CLIENTS=[{"client_id": "outline",
                   "client_secret": "...",
                   "display_name": "Makerspace Wiki",
                   "redirect_uris": ["https://wiki.example.com/auth/oidc.callback"]}]

Any number of clients may be listed. redirect_uris may also be written as a
single comma separated string, and is always matched exactly. display_name is
what the member sees on the login page and defaults to the client_id with
separators turned into spaces.
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
    display_name: str


def _parse_redirect_uris(value: object) -> list[str]:
    parts: list[object]
    if isinstance(value, str):
        parts = list(value.split(","))
    elif isinstance(value, list):
        parts = value
    else:
        raise ValueError("redirect_uris must be a list of strings, or a comma separated string")
    uris = [str(uri).strip() for uri in parts]
    uris = [uri for uri in uris if uri]
    if not uris:
        raise ValueError("redirect_uris must contain at least one URI")
    return uris


def default_display_name(client_id: str) -> str:
    """Human readable name for a client that did not configure a display_name."""
    words = [word for word in client_id.replace("_", " ").replace("-", " ").split(" ") if word]
    return " ".join(word[0].upper() + word[1:] for word in words) or client_id


def _parse_client(entry: object) -> OIDCClient:
    if not isinstance(entry, dict):
        raise ValueError("each client must be a JSON object")
    client_id = str(entry.get("client_id") or "")
    client_secret = str(entry.get("client_secret") or "")
    if not client_id:
        raise ValueError("client_id is required")
    if not client_secret:
        raise ValueError(f"client_secret is required for client {client_id}")
    display_name = str(entry.get("display_name") or "").strip()
    return OIDCClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uris=_parse_redirect_uris(entry.get("redirect_uris")),
        display_name=display_name or default_display_name(client_id),
    )


def _configured_clients_json() -> list[OIDCClient]:
    raw = config.config.get("OIDC_CLIENTS")
    if not raw or not raw.strip():
        return []
    try:
        entries = json.loads(raw)
        if not isinstance(entries, list):
            raise ValueError("OIDC_CLIENTS must be a JSON array of client objects")
        return [_parse_client(entry) for entry in entries]
    except (ValueError, TypeError) as e:
        # A misconfigured relying party must not take down unrelated clients,
        # so the whole list is dropped rather than raised to the request.
        logger.error(f"ignoring OIDC_CLIENTS: {e}")
        return []


def get_configured_clients() -> dict[str, OIDCClient]:
    """All configured relying parties, keyed by client_id."""
    clients: dict[str, OIDCClient] = {}
    for client in _configured_clients_json():
        if client.client_id in clients:
            logger.error(f"duplicate OIDC client_id {client.client_id} in configuration, ignoring the later one")
            continue
        clients[client.client_id] = client
    return clients


def validate_client_id(client_id: str) -> Optional[OIDCClient]:
    clients = get_configured_clients()
    if not clients:
        logger.warning("OIDC login attempted but no OIDC clients are configured")
        return None
    client = clients.get(client_id)
    if client is None:
        logger.warning(f"OIDC login attempted with unknown client_id {client_id}")
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
