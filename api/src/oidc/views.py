from datetime import datetime, timedelta, timezone
from logging import getLogger

from core.auth import generate_token
from core.models import AccessToken
from flask import Response, g, jsonify, request
from membership.membership import get_membership_summary
from membership.models import Member
from service.api_definition import GET, POST, PUBLIC, USER, Arg, non_empty_str
from service.db import db_session
from service.error import BadRequest, Unauthorized

from oidc import provider, service

logger = getLogger("makeradmin")


def oauth_error(error: str, description: str, status: int = 400, www_authenticate: bool = False) -> Response:
    """Error response in the format required by RFC 6749 section 5.2, which
    OAuth2 client libraries understand (unlike makeradmin's regular error
    format)."""
    response = jsonify(error=error, error_description=description)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    if www_authenticate:
        response.headers["WWW-Authenticate"] = 'Basic realm="makeradmin"'
    return response


@service.route("/authorize", method=POST, permission=USER)
def authorize(
    client_id=Arg(non_empty_str),
    redirect_uri=Arg(non_empty_str),
    state=Arg(str, required=False),
    response_type=Arg(str, required=False),
    scope=Arg(str, required=False),
):
    """Approve an OIDC authorization request for the logged in member.

    Called by the authorize page in the member portal. Returns the URL the
    browser should be redirected to (the relying party's redirect_uri with an
    authorization code attached).
    """
    if response_type is not None and response_type != "code":
        raise BadRequest("Only the authorization code flow is supported.", fields="response_type")

    client = provider.validate_client_id(client_id)
    if client is None:
        raise BadRequest("Unknown OIDC client.", fields="client_id")

    if redirect_uri not in client.redirect_uris:
        # Do not redirect to unregistered URIs: that would allow stealing codes.
        raise BadRequest("Redirect URI is not registered for this client.", fields="redirect_uri")

    redirect_to = provider.issue_authorization_code(g.user_id, client, redirect_uri, state)
    logger.info(f"issued oidc authorization code to member_id {g.user_id} for client {client.client_id}")
    return dict(redirect=redirect_to)


@service.route("/token", method=POST, permission=PUBLIC, flat_return=True)
def token(
    grant_type=Arg(str, required=False),
    code=Arg(str, required=False),
    client_id=Arg(str, required=False),
    client_secret=Arg(str, required=False),
    redirect_uri=Arg(str, required=False),
):
    """OAuth2 token endpoint: exchange an authorization code for an access token.

    Errors are returned in the RFC 6749 format rather than makeradmin's usual
    one, since the caller is an OAuth2 client library.
    """
    if grant_type is None:
        return oauth_error("invalid_request", "Missing grant_type parameter.")
    if grant_type != "authorization_code":
        return oauth_error("unsupported_grant_type", "Only the authorization_code grant type is supported.")
    if not code:
        return oauth_error("invalid_request", "Missing code parameter.")

    # Client credentials arrive in the POST body or as HTTP Basic auth.
    basic = request.authorization
    used_basic_auth = basic is not None and basic.type == "basic"
    if used_basic_auth:
        client_id = client_id or basic.username
        client_secret = client_secret or basic.password

    client = provider.validate_client_credentials(client_id or "", client_secret or "")
    if client is None:
        return oauth_error("invalid_client", "Invalid client credentials.", 401, www_authenticate=used_basic_auth)

    member_id = provider.redeem_authorization_code(code, client, redirect_uri)
    if member_id is None:
        return oauth_error("invalid_grant", "Invalid, expired or already used authorization code.")

    access_token = AccessToken(
        user_id=member_id,
        access_token=generate_token(),
        browser=f"oidc client {client.client_id}",
        ip=request.remote_addr,
        expires=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=provider.ACCESS_TOKEN_TTL_SECONDS),
        lifetime=provider.ACCESS_TOKEN_TTL_SECONDS,
    )
    db_session.add(access_token)

    logger.info(f"issued oidc access token to member_id {member_id} for client {client.client_id}")
    return dict(
        access_token=access_token.access_token,
        token_type="Bearer",
        expires_in=provider.ACCESS_TOKEN_TTL_SECONDS,
    )


@service.route("/userinfo", method=GET, permission=USER, flat_return=True)
def userinfo():
    """OIDC userinfo endpoint: standard claims for the authenticated member."""
    member = db_session.get(Member, g.user_id)
    if member is None or member.deleted_at is not None:
        raise Unauthorized("Member not found.")

    summary = get_membership_summary(member.member_id)
    name = f"{member.firstname} {member.lastname}".strip() if member.lastname else member.firstname

    return dict(
        sub=str(member.member_id),
        email=member.email,
        email_verified=True,
        name=name,
        given_name=member.firstname,
        family_name=member.lastname,
        preferred_username=str(member.member_number),
        member_number=member.member_number,
        membership_active=summary.membership_active,
        labaccess_active=summary.effective_labaccess_active,
    )
