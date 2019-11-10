from flask import request

from membership.member_auth import check_and_hash_password
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError


def handle_password(data):
    data.pop('password', None)
    unhashed_password = data.pop('unhashed_password', None)
    data['password'] = check_and_hash_password(unhashed_password)

    
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
