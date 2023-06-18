from typing import Optional
from flask import request
from membership.models import Member

from membership.member_auth import check_and_hash_password
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError
from logging import getLogger


logger = getLogger('makeradmin')


def handle_password(data):
    data.pop('password', None)
    unhashed_password = data.pop('unhashed_password', None)
    if unhashed_password is not None:
        data['password'] = check_and_hash_password(unhashed_password)

class RaceCondition(Exception):
    pass

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
                    max_member_number, = db_session.execute("SELECT COALESCE(MAX(member_number), 999) FROM membership_members").fetchone()
                    data['member_number'] = max_member_number + 1
                    obj = self.to_obj(self._create_internal(data, commit=commit))
                    logger.info(f"created member with number {data['member_number']}")
                    if db_session.query(self.model).filter(Member.member_number == data['member_number']).count() != 1:
                        raise RaceCondition()
                    return obj
            except RaceCondition as e:
                print("Race condition when creating member, retrying...")
                # Try again
                continue

    def update(self, entity_id: int, commit=True):
        data = request.json or {}
        handle_password(data)
        return self._update_internal(entity_id, data, commit=commit)

    def delete(self, entity_id: int, commit=False) -> None:
        # Do an import here to avoid circular imports
        from shop import stripe_subscriptions
        # Ensure that if a member is deleted, all of their stripe data is deleted as well (including subscriptions)
        # Note: This will throw NotFound if the member doesn't exist, which is fine.
        stripe_subscriptions.delete_stripe_customer(entity_id)
        return super().delete(entity_id, commit)
