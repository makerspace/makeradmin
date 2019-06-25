from flask import request

from membership.member_auth import hash_password
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError, UnprocessableEntity


ALPHA_LOWER_SET = set("abcdefghijklmnopqrstuvwxyzåäö")
ALPHA_UPPER_SET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ")
DIGIT_SET = set("0123456789")
ALPHA_DIGIT_SET = ALPHA_LOWER_SET | ALPHA_UPPER_SET | DIGIT_SET

forbidden_sub_sequences = [
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


def handle_password(data):
    password = data.pop('password', None)
    unhashed_password = data.pop('unhashed_password', None)
    if unhashed_password is not None:
        contained_chars_set = set(unhashed_password)

        if len(unhashed_password) < 8 or len(contained_chars_set) < 6:
            raise ValueError("password must be at least 8 characters long with at least 6 unique characters")

        # Test for forbidden sequences
        forbidden_sequences = {
            "password", "q1w2e3r4t5", "maker", "space"
        }
        if (
                any([contains_sub_sequence(unhashed_password, s, l) for s, l in forbidden_sub_sequences]) or
                any([unhashed_password.find(s) != -1 for s in forbidden_sequences])
        ):
            raise ValueError("password contains a forbidden sequence of characters")

        data['password'] = hash_password(unhashed_password)
        
    
class MemberEntity(Entity):
    """
    Special handling of Member, requires subclassing entity:
    
    * Member member_number should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock.
    
    * Unhashed password should be hashed on save.
    """
    
    def create(self, data=None, commit=True):
        if data is None:
            data = request.json or {}
            
        handle_password(data)
        
        status, = db_session.execute("SELECT GET_LOCK('member_number', 20)").fetchone()
        if not status:
            raise InternalServerError("Failed to create member, try again later.",
                                      log="failed to aquire member_number lock")
        try:
            if data.get('member_number') is None:
                sql = "SELECT COALESCE(MAX(member_number), 999) FROM membership_members"
                max_member_number, = db_session.execute(sql).fetchone()
                data['member_number'] = max_member_number + 1
            obj = self.to_obj(self._create_internal(data, commit=commit))
            return obj
        except Exception:
            # Rollback session if anything went wrong or we can't release the lock.
            db_session.rollback()
            raise
        finally:
            db_session.execute("DO RELEASE_LOCK('member_number')")

    def update(self, entity_id, commit=True):
        data = request.json or {}
        handle_password(data)
        return self._update_internal(entity_id, data, commit=commit)
