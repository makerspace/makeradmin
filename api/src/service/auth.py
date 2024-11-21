from datetime import datetime, timedelta, timezone

import membership.member_auth
from core.models import AccessToken
from core.service_users import SERVICE_PERMISSIONS
from flask import g, request

from service.api_definition import BAD_VALUE, EXPIRED, REQUIRED, USER
from service.db import db_session
from service.error import BadRequest, Unauthorized


def authenticate_request() -> None:
    """Update global object with user_id and user permissions using token from request header."""

    # Make sure user_id and permissions is always set.
    g.user_id = None
    g.permissions = tuple()

    # logger.info("DATA " + repr(request.get_data()))
    # logger.info("HEADERS " + repr(request.headers))
    # logger.info("ARGS " + repr(request.args))
    # logger.info("FORM " + repr(request.form))
    # logger.info("JSON " + repr(request.json))

    authorization = request.headers.get("Authorization", None)
    if authorization is None:
        return

    bearer = "Bearer "
    if not authorization.startswith(bearer):
        raise Unauthorized("Unauthorized, can't find credentials.", fields="bearer", what=REQUIRED)

    token = authorization[len(bearer) :].strip()

    access_token = db_session.query(AccessToken).get(token)
    if not access_token:
        raise Unauthorized("Unauthorized, invalid access token.", fields="bearer", what=BAD_VALUE)

    now = datetime.now(timezone.utc)
    if access_token.expires < now:
        db_session.query(AccessToken).filter(AccessToken.expires < now).delete()
        raise Unauthorized("Unauthorized, expired access token.", fields="bearer", what=EXPIRED)

    if access_token.permissions is None:
        if access_token.user_id < 0:
            permissions = SERVICE_PERMISSIONS.get(access_token.user_id, [])

        elif access_token.user_id > 0:
            permissions_set = {p for _, p in membership.member_auth.get_member_permissions(access_token.user_id)}
            permissions_set.add(USER)
            permissions = list(permissions_set)

        else:
            raise BadRequest(
                "Bad token.", log=f"access_token {access_token.access_token} has user_id 0, this should never happend"
            )

        access_token.permissions = ",".join(permissions)

    access_token.ip = request.remote_addr
    access_token.browser = request.user_agent.string
    access_token.expires = datetime.now(timezone.utc) + timedelta(seconds=access_token.lifetime)

    g.user_id = access_token.user_id
    g.session_token = access_token.access_token
    g.permissions = access_token.permissions.split(",")

    # Commit token validation to make it stick even if request fails later.
    db_session.commit()
