from flask import request
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError
from sqlalchemy import func, text


class OrderedEntity(Entity):
    """
    Special handling of entity with display_order field:

    * display_order should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock.
    """

    def create(self, data: dict | None = None, commit: bool = True) -> dict:
        if data is None:
            data = request.json or {}

        # Lock the rows for update to prevent race conditions
        max_display_order = db_session.query(func.max(self.model.display_order)).with_for_update().scalar()
        if data.get("display_order") is None:
            data["display_order"] = (max_display_order or 0) + 1
        try:
            obj = self.to_obj(self._create_internal(data, commit=commit))
            return obj
        except Exception:
            db_session.rollback()
            raise
