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

// Mail
$app->group(array(), function() use ($app)
{
	$app->   get("messages",      "Mail@list");   // Get collection
	$app->  post("messages",      "Mail@create"); // Model: Create
	$app->   get("messages/{id}", "Mail@read");   // Model: Read
	$app->   put("messages/{id}", "Mail@update"); // Model: Update
	$app->delete("messages/{id}", "Mail@delete"); // Model: Delete
	$app->  post("messages/send", "Mail@send");   // Add E-mail to send queue
});