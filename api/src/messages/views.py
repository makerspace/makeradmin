


# Templates
# TODO $app->   get("messages/templates",      ['middleware' => 'permission:message_view', 'uses' => "Template@list"]);   // Get collection
# TODO $app->  post("messages/templates",      ['middleware' => 'permission:message_send', 'uses' => "Template@create"]); // Model: Create
# TODO $app->   get("messages/templates/{id}", ['middleware' => 'permission:message_view', 'uses' => "Template@read"]);   // Model: Read
# TODO $app->   put("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@update"]); // Model: Update
# TODO $app->delete("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@delete"]); // Model: Delete


# Messages
# TODO $app-> get("messages/message",      ['middleware' => 'permission:message_view', 'uses' => "Message@list"]);     // Get collection (List sent messages)
# TODO $app->post("messages/message",      ['middleware' => 'permission:message_send', 'uses' => "Message@create"]);   // Model: Create (Send new message)
# TODO $app-> get("messages/message/{id}", ['middleware' => 'permission:message_view', 'uses' => "Message@read"]);     // Model: Read (Get sent message)


# Message recipients
# TODO $app-> get("messages/message/user/{id}",       ['middleware' => 'permission:message_view', 'uses' => "Recipient@userlist"]); // Get collection (List sent messages for specific user)
# TODO $app-> get("messages/message/{id}/recipients", ['middleware' => 'permission:message_view', 'uses' => "Recipient@list"]);   // Get collection (List recipients in sent message)
