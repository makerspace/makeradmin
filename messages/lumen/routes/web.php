<?php

/*
|--------------------------------------------------------------------------
| Application Routes
|--------------------------------------------------------------------------
|
| Here is where you can register all of the routes for an application.
| It is a breeze. Simply tell Lumen the URIs it should respond to
| and give it the Closure to call when that URI is requested.
|
*/

$app->group(array(), function() use ($app)
{
	// Templates
	$app->   get("messages/templates",      ['middleware' => 'permission:message_view', 'uses' => "Template@list"]);   // Get collection
	$app->  post("messages/templates",      ['middleware' => 'permission:message_send', 'uses' => "Template@create"]); // Model: Create
	$app->   get("messages/templates/{id}", ['middleware' => 'permission:message_view', 'uses' => "Template@read"]);   // Model: Read
	$app->   put("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@update"]); // Model: Update
	$app->delete("messages/templates/{id}", ['middleware' => 'permission:message_send', 'uses' => "Template@delete"]); // Model: Delete

	// Messages
	$app-> get("messages",                 ['middleware' => 'permission:message_view', 'uses' => "Message@list"]);     // Get collection (List sent messages)
	$app->post("messages",                 ['middleware' => 'permission:message_send', 'uses' => "Message@create"]);   // Model: Create (Send new message)
	$app-> get("messages/{id}",            ['middleware' => 'permission:message_view', 'uses' => "Message@read"]);     // Model: Read (Get sent message)

	// Recipients
	$app-> get("messages/user/{id}",       ['middleware' => 'permission:message_view', 'uses' => "Recipient@userlist"]); // Get collection (List sent messages for specific user)
	$app-> get("messages/{id}/recipients", ['middleware' => 'permission:message_view', 'uses' => "Recipient@list"]);   // Get collection (List recipients in sent message)
});