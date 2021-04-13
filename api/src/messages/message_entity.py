from flask import request

from membership.models import Member, member_group
from service.api_definition import BAD_VALUE, natural1
from service.db import db_session
from service.entity import Entity
from service.error import UnprocessableEntity


class MessageEntity(Entity):

    def create_message(self, data, commit=True):

        # Validate and fetch recipients.

        recipients = data.pop('recipients', [])
        if not isinstance(recipients, list):
            raise UnprocessableEntity("Recipients should be a list.")

        member_ids = set()
        
        for recipient in recipients:
            type_ = recipient.get('type')
            if type_ not in ('member', 'group'):
                raise UnprocessableEntity(what=BAD_VALUE, message='Recipient type should be member or group')
                
            try:
                id_ = natural1(recipient.get('id'))
            except (ValueError, TypeError):
                raise UnprocessableEntity(what=BAD_VALUE, message=f'Recipient id should be positive int.')
            
            if type_ == 'member':
                member_ids.add(id_)
            else:
                member_ids.update(
                    {i for i, in db_session.query(member_group.c.member_id).filter(member_group.c.group_id == id_)}
                )
        
        members = db_session.query(Member).filter(Member.member_id.in_(member_ids)).all()
        
        if len(members) != len(member_ids):
            raise UnprocessableEntity('Recipient id is missing in the database.')
        
        for member in members:
            message = self._create_internal({
                **data,
                'recipient': member.email,
                'member_id': member.member_id,
                'status': 'queued'
            }, commit=False)
        
        if commit:
            db_session.commit()
        
        return message
    
    def create(self, data=None, commit=True):
        """
        Create is used to send message to a list of recipients. Recipients should be a list of objects with id,
        type where type is member or group. The rest of the data is used to create the message normally.
        """
        
        if data is None:
            data = request.json or {}
        
        obj = self.to_obj(self.create_message(data, commit=commit))
        obj['member_id'] = None
        obj['recipient'] = None
        return obj
