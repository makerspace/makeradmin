from flask import request
import pymysql
from sqlalchemy.exc import IntegrityError
from pymysql.constants.ER import DUP_ENTRY
from membership.models import Member

from membership.member_auth import check_and_hash_password
from service.db import db_session
from service.entity import Entity
from logging import getLogger


logger = getLogger('makeradmin')


def handle_password(data):
    data.pop('password', None)
    unhashed_password = data.pop('unhashed_password', None)
    if unhashed_password is not None:
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

        assert 'member_number' not in data
        # Locking was used here previously, but that did not work well with transactions
        # so now we use transactions to solve EVERYTHING.
        # In practice we will never get a race here, except possibly in tests that run in parallel.
        while True:
            try:
                with db_session.begin_nested():
                    data = data.copy()
                    max_member_number, = db_session.execute("SELECT COALESCE(MAX(member_number), 999) FROM membership_members").fetchone()
                    data['member_number'] = max_member_number + 1
                    # We must not commit here, because that will end our transaction, and the to_obj call will fail
                    member: Member = self._create_internal(data, commit=False)
                    logger.info(f"created member with number {member.member_number}")

                    obj = self.to_obj(member)
                    if commit:
                        db_session.commit()
                    return obj
            except IntegrityError as e:
                # Check if we have got a duplicate member number
                if isinstance(e.orig, pymysql.err.IntegrityError):
                    errno, error = e.orig.args
                    if errno == DUP_ENTRY and "membership_members_member_number_index" in error:
                        print("Race condition when creating member, retrying...")
                        continue
                    else:
                        raise e
                else:
                    raise e

    def update(self, entity_id: int, commit=True):
        data = request.json or {}
        handle_password(data)
        return self._update_internal(entity_id, data, commit=commit)

    def delete(self, entity_id: int, commit: bool = False) -> None:
        # Do an import here to avoid circular imports
        from shop import stripe_subscriptions

        # Ensure that if a member is deleted, all of their stripe data is deleted as well (including subscriptions)
        stripe_subscriptions.delete_stripe_customer(entity_id)
        return super().delete(entity_id, commit)
