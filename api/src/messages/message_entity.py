from flask import request

from membership.member_auth import hash_password
from membership.models import Member, Group, member_group
from messages.models import Recipient
from service.api_definition import BAD_VALUE, Enum, natural1, REQUIRED
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError, UnprocessableEntity
from service.logging import logger

example = {
   "date_sent": None,
   "recipients": [
      {
         "id": 4,
         "value": "member4",
         "type": "member",
         "label": "Medlem: Anders Roos (#1003)"
      },
      {
         "type": "member",
         "label": "Medlem: Anders Roos2 (#1029)",
         "value": "member30",
         "id": 30
      }
   ],
   "message_type": "email",
   "num_recipients": 0,
   "entity_id": 0,
   "updated_at": None,
   "subject": "Hej",
   "created_at": None,
   "recipient": "",
   "message_id": 0,
   "body": "dasdasdas",
   "recipient_id": 0,
   "status": ""
}


def execute_template(member, text):
    return (
        text.replace("##member_number##", member.member_number)
            .replace("##member_id##", member.member_id)
            .replace("##firstname##", member.firstname)
            .replace("##lastname##", member.lastname)
            .replace("##email##", member.email)
    )


class MessageEntity(Entity):
    
    def create(self):
        """
        Create is used to send message to a list of recipients. Recipients should be a list of objects with id,
        type where type is member or group. The rest of the data is used to create the message normally.
        """
        
        data = request.json or {}
        
        # Create message.
        
        data['status'] = 'queued'
        
        message = self._create_internal(data)

        # Validate and create recipients.

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
                raise UnprocessableEntity(what=BAD_VALUE, message=f'Recipient id should be positived int.')
            
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
            recipient = Recipient(
                messages_message_id=message.messages_message_id,
                title=execute_template(member, message.title),
                description=execute_template(member, message.description),
                member_id=member.member_id,
                recipient=member.email,
                status=member.status,
            )
            db_session.add(recipient)
        
        return self.to_obj(message)
