import secrets
from datetime import datetime, timedelta
from string import ascii_letters, digits

from flask import g, request

import membership
from core.models import Login, AccessToken
from service.api_definition import SERVICE, USER, REQUIRED, BAD_VALUE, EXPIRED
from service.db import db_session
from service.error import TooManyRequests, ApiError, NotFound, Unauthorized


def generate_token():
    return ''.join(secrets.choice(ascii_letters + digits) for _ in range(32))


def create_access_token(ip, browser, user_id):
    assert user_id > 0
    
    access_token = AccessToken(
        user_id=user_id,
        access_token=generate_token(),
        browser=browser,
        ip=ip,
        expires=datetime.utcnow() + timedelta(minutes=5),
        lifetime=int(timedelta(days=14).total_seconds()),
    )
    
    db_session.add(access_token)
    
    return dict(access_token=access_token.access_token, expires=access_token.expires.isoformat())


def login(ip, browser, username, password):
    
    count = Login.get_failed_login_count(ip)
    
    if count > 10:
        raise TooManyRequests("Your have reached your maximum number of failed login attempts for the last hour."
                              " Please try again later.")

    try:
        data = membership.service.service_post('/authenticate', username=username, password=password)
        member_id = data.get('member_id')
    except ApiError:
        Login.register_login_failed(ip)
        raise
    
    Login.register_login_success(ip, member_id)

    return create_access_token(ip, browser, member_id)


def force_login(ip, browser, user_id):
    Login.register_login_success(ip, user_id)
    return create_access_token(ip, browser, user_id)


def remove_token(token, user_id):
    assert user_id > 0
    
    count = db_session\
        .query(AccessToken)\
        .filter(AccessToken.user_id == user_id, AccessToken.access_token == token)\
        .delete()
    
    if not count:
        raise NotFound("The access_token you specified could not be found in the database.")
        
    return None


def list_for_user(user_id):
    return [dict(
        access_token=access_token.access_token,
        browser=access_token.browser,
        ip=access_token.ip,
        expires=access_token.expires.isoformat(),
    ) for access_token in db_session.query(AccessToken).filter(AccessToken.user_id == user_id)]


def authenticate_request():
    """ Update global object with user_id and user permissions using token from request header. """
    
    # Make sure user_id and permissions is always set.
    g.user_id = None
    g.permissions = tuple()

    # logger.info("DATA " + repr(request.get_data()))
    # logger.info("HEADERS " + repr(request.headers))
    # logger.info("ARGS " + repr(request.args))
    # logger.info("FORM " + repr(request.form))
    # logger.info("JSON " + repr(request.json))
    
    authorization = request.headers.get('Authorization', None)
    if authorization is None:
        return

    bearer = 'Bearer '
    if not authorization.startswith(bearer):
        raise Unauthorized("Unauthorized, can't find credentials.", fields="bearer", what=REQUIRED)
        
    token = authorization[len(bearer):].strip()
    
    access_token = db_session.query(AccessToken).get(token)
    if not access_token:
        raise Unauthorized("Unauthorized, invalid access token.", fields="bearer", what=BAD_VALUE)
    
    now = datetime.utcnow()
    if access_token.expires < now:
        db_session.query(AccessToken).filter(AccessToken.expires < now).delete()
        raise Unauthorized("Unauthorized, expired access token.", fields="bearer", what=EXPIRED)
    
    if access_token.permissions is None:
        permissions = {
            p['permission'] for p in membership.service.service_get(f'/member/{access_token.user_id}/permissions')
        }
        if access_token.user_id < 0:
            permissions.add(SERVICE)
        else:
            permissions.add(USER)
            
        access_token.permissions = ','.join(permissions)
    
    access_token.ip = request.remote_addr
    access_token.browser = request.user_agent.string
    access_token.expires = datetime.utcnow() + timedelta(seconds=access_token.lifetime)
    
    g.user_id = access_token.user_id
    g.permissions = access_token.permissions.split(',')
    
    # Commit token validation to make it stick even if request fails later.
    db_session.commit()
