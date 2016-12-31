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
	$app->   get("messages/templates",      "Template@list");   // Get collection
	$app->  post("messages/templates",      "Template@create"); // Model: Create
	$app->   get("messages/templates/{id}", "Template@read");   // Model: Read
	$app->   put("messages/templates/{id}", "Template@update"); // Model: Update
	$app->delete("messages/templates/{id}", "Template@delete"); // Model: Delete

	// Messages
	$app-> get("messages",                 "Message@list");     // Get collection (List sent messages)
	$app->post("messages",                 "Message@create");   // Model: Create (Send new message)
	$app-> get("messages/{id}",            "Message@read");     // Model: Read (Get sent message)

	// Recipients
	$app-> get("messages/user/{id}",       "Recipient@userlist"); // Get collection (List sent messages for specific user)
	$app-> get("messages/{id}/recipients", "Recipient@list");   // Get collection (List recipients in sent message)
});