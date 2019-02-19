from flask import request

from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError


class OrderedEntity(Entity):
    """
    Special handling of entity with display_order field:
    
    * display_order should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock.
    """
    
    def create(self):
        data = request.json or {}
        
        status, = db_session.execute("SELECT GET_LOCK('display_order', 20)").fetchone()
        if not status:
            raise InternalServerError("Failed to create, try again later.",
                                      log="failed to aquire display_order lock")
        try:
            if data.get('display_order') is None:
                sql = f"SELECT COALESCE(MAX(display_order), 0) FROM {self.model.table_name}"
                max_member_number, = db_session.execute(sql).fetchone()
                data['display_order'] = max_member_number + 1
            obj = self.to_obj(self._create_internal(data))
            db_session.commit()
            return obj
        except Exception:
            # Rollback session if anything went wrong or we can't release the lock.
            db_session.rollback()
            raise
        finally:
            db_session.execute("DO RELEASE_LOCK('display_order')")
