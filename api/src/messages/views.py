from messages import service
from messages.message_entity import MessageEntity
from messages.models import Message, Template, Recipient
from service.api_definition import MESSAGE_VIEW, MESSAGE_SEND
from service.entity import Entity, not_empty, OrmSingeRelation

message_entity = MessageEntity(
    Message,
    validation=dict(title=not_empty),
    search_columns=('title', 'description'),
)

template_entity = Entity(
    Template,
    search_columns=('name', 'title', 'description'),
)

recipient_entity = Entity(Recipient)

service.entity_routes(
    path="/message",
    entity=message_entity,
    permission_list=MESSAGE_VIEW,
    permission_read=MESSAGE_VIEW,
    permission_create=MESSAGE_SEND,  # TODO Create is doing something  really special, check this code.
)

service.related_entity_routes(
    path="/message/<int:related_entity_id>/recipients",
    entity=recipient_entity,
    relation=OrmSingeRelation('message_recipients', 'messages_message_id'),
    permission_list=MESSAGE_VIEW,
)

service.entity_routes(
    path="/templates",
    entity=template_entity,
    permission_list=MESSAGE_VIEW,
    permission_read=MESSAGE_VIEW,
    permission_create=MESSAGE_SEND,
    permission_update=MESSAGE_SEND,
    permission_delete=MESSAGE_SEND,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/recipients",
    entity=recipient_entity,
    relation=OrmSingeRelation('member_recipients', 'member_id'),
    permission_list=MESSAGE_VIEW,
)
