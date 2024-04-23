from typing import List, Optional, Tuple

import bcrypt
import sqlalchemy
from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import Unauthorized

from membership.models import Group, Member, Permission

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
    ("password", None),
    ("q1w2e3", None),
    ("maker", None),
    ("space", None),
    ("dinmamma", None),
]


def contains_sub_sequence(value: str, sequence: str, length: Optional[int]) -> bool:
    if length is None:
        length = len(sequence)
    value = value.lower()
    for i in range(0, len(sequence) - length + 1):
        if value.find(sequence[i : i + length]) != -1:
            return True
    return False


def verify_password(password: Optional[str], password_hash: Optional[str]) -> bool:
    if not password or not password_hash:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()


def check_and_hash_password(unhashed_password: Optional[str]) -> Optional[str]:
    if unhashed_password is None:
        return None

    contained_chars_set = set(unhashed_password)

    if len(unhashed_password) < 8 or len(contained_chars_set) < 6:
        raise ValueError("Password must be at least 8 characters long with at least 6 unique characters.")

    # Test for forbidden sequences
    if any(contains_sub_sequence(unhashed_password, sequence, length) for sequence, length in FORBIDDEN_SUB_SEQUENCES):
        raise ValueError("Password contains a forbidden sequence of characters, try something less common.")

    return hash_password(unhashed_password)


def get_member_permissions(member_id: Optional[int] = None) -> List[Tuple[int, str]]:
    """Return query to get all (permission_id, permission) for a memeber, used from core."""
    return (
        db_session.query(Permission.permission_id, Permission.permission)
        .distinct()
        .join(Group, Permission.groups)
        .join(Member, Group.members)
        .filter_by(member_id=member_id)
    )


def authenticate(username: Optional[str] = None, password: Optional[str] = None) -> int:
    """Authenticate a member trough email/member number and password, returns member_id if authenticated, used from core."""
    member: Optional[Member] = (
        db_session.query(Member)
        .filter((Member.email == username) | (sqlalchemy.cast(Member.member_number, sqlalchemy.String) == username))
        .first()
    )

    if member is None or not verify_password(password, member.password):
        raise Unauthorized(
            "The email/member number and/or password you specified was incorrect.",
            fields="username,password",
            what=BAD_VALUE,
        )

    return member.member_id
