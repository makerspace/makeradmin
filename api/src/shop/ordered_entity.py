from flask import request
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError
from sqlalchemy import func


class OrderedEntity(Entity):
    """
    Special handling of entity with display_order field:

    * display_order should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock.
    """

    def create(self, data=None, commit=True):
        if data is None:
            data = request.json or {}

        (status,) = db_session.execute("SELECT GET_LOCK('display_order', 20)").fetchone()
        if not status:
            raise InternalServerError("Failed to create, try again later.", log="failed to aquire display_order lock")
        try:
            if data.get("display_order") is None:
                data["display_order"] = (db_session.query(func.max(self.model.display_order)).scalar() or 0) + 1
            obj = self.to_obj(self._create_internal(data, commit=commit))
            return obj
        except Exception:
            # Rollback session if anything went wrong or we can't release the lock.
            db_session.rollback()
            raise
        finally:
            db_session.execute("DO RELEASE_LOCK('display_order')")
