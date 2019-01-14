import bcrypt

from membership.models import Permission, Group, Member
from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import Unauthorized


def get_member_permissions(member_id=None):
    """ Return query to get all (permission_id, permission) for a memeber, used from core. """
    return (
        db_session
            .query(Permission.permission_id, Permission.permission)
            .distinct()
            .join(Group, Permission.groups)
            .join(Member, Group.members)
            .filter_by(member_id=member_id)
    )


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_password(password):
    # TODO BM When is this supposed to be used? Think passwords should be hashed on save?
    bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())


def authenticate(username=None, password=None):
    """ Authenticate a member trough username and password, returns member_id if authenticated, used from core. """
    
    member = db_session.query(Member).filter_by(email=username).first()
    
    if not member or not verify_password(password, member.password):
        raise Unauthorized("The username and/or password you specified was incorrect.",
                           fields='username,password', what=BAD_VALUE)
    
    return member.member_id
