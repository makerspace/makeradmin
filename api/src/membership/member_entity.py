from flask import request

from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError


class MemberEntity(Entity):
    """ Member member_number should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock. """
    
    def create(self):
        status, = db_session.execute("SELECT GET_LOCK('member_number', 20)").fetchone()
        if not status:
            raise InternalServerError("Failed to create member, try again later.",
                                      log="failed to aquire member_number lock")
        
        try:
            data = request.json or {}
            if data.get('member_number') is None:
                sql = "SELECT COALESCE(MAX(member_number), 999) FROM membership_members"
                max_member_number, = db_session.execute(sql).fetchone()
                data['member_number'] = max_member_number + 1
            return self._create_internal(data)
        except Exception:
            # Rollback session if anything went wrong or we can't release the lock.
            db_session.rollback()
            raise
        finally:
            db_session.execute("DO RELEASE_LOCK('member_number')")
        
        
