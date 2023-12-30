from service.api_definition import MESSAGE_SEND, MESSAGE_VIEW
from service.entity import OrmSingeRelation, not_empty

from messages import service
from messages.message_entity import MessageEntity
from messages.models import Message

message_entity = MessageEntity(
    Message,
    validation=dict(title=not_empty),
    search_columns=("subject", "body", "recipient"),
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
    relation=OrmSingeRelation("member_messages", "member_id"),
    permission_list=MESSAGE_VIEW,
)
