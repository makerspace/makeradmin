import bcrypt

from membership.models import Permission, Group, Member
from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import Unauthorized


ALPHA_LOWER_SET = set("abcdefghijklmnopqrstuvwxyzåäö")
ALPHA_UPPER_SET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ")
DIGIT_SET = set("0123456789")
ALPHA_DIGIT_SET = ALPHA_LOWER_SET | ALPHA_UPPER_SET | DIGIT_SET

FORBIDDEN_SUB_SEQUENCES = [
    ("abcdefghijklmnopqrstuvwxyzåäö", 4),
    ("abcdefghijklmnopqrstuvwxyzåäö"[::-1], 4),
    ("qwertyuiopå", 4),
    ("qwertyuiopå"[::-1], 4),
    ("asdfghjklöä", 4),
    ("asdfghjklöä"[::-1], 4),
    ("zxcvbnm,.", 4),
    ("zxcvbnm,."[::-1], 4),
    ("01234567890", 3),
    ("01234567890"[::-1], 3),
]


def contains_sub_sequence(value, sequence, length):
    for i in range(0, len(sequence) - length + 1):
        if value.find(sequence[i:i + length]) != -1:
            return True
    return False


def verify_password(password, password_hash):
    if not password or not password_hash:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_password(password):
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()


def check_and_hash_password(unhashed_password):
    if unhashed_password is None:
        return None
        
    contained_chars_set = set(unhashed_password)

    if len(unhashed_password) < 8 or len(contained_chars_set) < 6:
        raise ValueError("password must be at least 8 characters long with at least 6 unique characters")

    # Test for forbidden sequences
    forbidden_sequences = {
        "password", "q1w2e3r4t5", "maker", "space"
    }
    if (
            any([contains_sub_sequence(unhashed_password, s, l) for s, l in FORBIDDEN_SUB_SEQUENCES]) or
            any([unhashed_password.find(s) != -1 for s in forbidden_sequences])
    ):
        raise ValueError("password contains a forbidden sequence of characters, try something less common")

    return hash_password(unhashed_password)


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


def authenticate(username=None, password=None):
    """ Authenticate a member trough username and password, returns member_id if authenticated, used from core. """
    
    member = db_session.query(Member).filter_by(email=username).first()
    
    if not member or not verify_password(password, member.password):
        raise Unauthorized("The username and/or password you specified was incorrect.",
                           fields='username,password', what=BAD_VALUE)
    
    return member.member_id
