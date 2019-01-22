from messages import service
from messages.models import Message
from service.api_definition import MESSAGE_VIEW, MESSAGE_SEND
from service.entity import Entity, not_empty

message_entity = Entity(
    Message,
    validation=dict(title=not_empty),
    search_columns=('title', 'description'),
)

service.entity_routes(
    path="/message",
    entity=message_entity,
    permission_list=MESSAGE_VIEW,
    permission_read=MESSAGE_VIEW,
    permission_create=MESSAGE_SEND,  # TODO Create is doing something  really special, check this code.
)

# Templates
# TODO $app->   get("messages/templates",      ['middleware' => 'permission:message_view', 'uses' => "Template@list"]);   // Get collection
# TODO $app->  post("messages/templates",      ['middleware' => 'permission:message_send', 'uses' => "Template@create"]); // Model: Create
# TODO $app->   get("messages/templates/{id}", ['middleware' => 'permission:message_view', 'uses' => "Template@read"]);   // Model: Read
# TODO $app->   put("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@update"]); // Model: Update
# TODO $app->delete("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@delete"]); // Model: Delete

# Message recipients
# TODO $app-> get("messages/message/user/{id}",       ['middleware' => 'permission:message_view', 'uses' => "Recipient@userlist"]); // Get collection (List sent messages for specific user)
# TODO $app-> get("messages/message/{id}/recipients", ['middleware' => 'permission:message_view', 'uses' => "Recipient@list"]);   // Get collection (List recipients in sent message)
