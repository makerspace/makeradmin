from service.db import db_session
from sqlalchemy.exc import IntegrityError

from membership.models import Permission


def register_permissions(permissions):
    for permission in permissions:
        try:
            db_session.add(Permission(permission=permission))
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
