from messages import service
from messages.models import Message, Template
from service.api_definition import MESSAGE_VIEW, MESSAGE_SEND, GET
from service.entity import Entity, not_empty

message_entity = Entity(
    Message,
    validation=dict(title=not_empty),
    search_columns=('title', 'description'),
)

template_entity = Entity(
    Template,
    search_columns=('name', 'title', 'description'),
)

service.entity_routes(
    path="/message",
    entity=message_entity,
    permission_list=MESSAGE_VIEW,
    permission_read=MESSAGE_VIEW,
    permission_create=MESSAGE_SEND,  # TODO Create is doing something  really special, check this code.
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


@service.route("/message/user/<int:member_id>", method=GET, permission=MESSAGE_VIEW)
def member_user_list(member_id=None):
    # TODO $app-> get("messages/message/user/{id}",       ['middleware' => 'permission:message_view', 'uses' => "Recipient@userlist"]); // Get collection (List sent messages for specific user)
    pass


@service.route("/message/<int:message_id>/recipients", method=GET, permission=MESSAGE_VIEW)
def member_list_message_recipients(message_id=None):
    # TODO $app-> get("messages/message/{id}/recipients", ['middleware' => 'permission:message_view', 'uses' => "Recipient@list"]);   // Get collection (List recipients in sent message)
    pass
