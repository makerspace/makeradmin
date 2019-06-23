from messages import service
from messages.message_entity import MessageEntity
from messages.models import Message
from service.api_definition import MESSAGE_VIEW, MESSAGE_SEND
from service.entity import not_empty, OrmSingeRelation


message_entity = MessageEntity(
    Message,
    validation=dict(title=not_empty),
    search_columns=('subject', 'body'),
)


service.entity_routes(
    path="/message",
    entity=message_entity,
    permission_list=MESSAGE_VIEW,
    permission_read=MESSAGE_VIEW,
    permission_create=MESSAGE_SEND,
)


service.related_entity_routes(
    path="/member/<int:related_entity_id>/messages",
    entity=message_entity,
    relation=OrmSingeRelation('member_messages', 'member_id'),
    permission_list=MESSAGE_VIEW,
)
