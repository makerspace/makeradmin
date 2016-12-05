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

$app->get('/', function () use ($app) {
	return $app->version();
});

// Mail
$app->group(array("namespace" => "App\Http\Controllers"), function() use ($app)
{
	$app->   get("mail",      "Mail@list");   // Get collection
	$app->  post("mail",      "Mail@create"); // Model: Create
	$app->   get("mail/{id}", "Mail@read");   // Model: Read
	$app->   put("mail/{id}", "Mail@update"); // Model: Update
	$app->delete("mail/{id}", "Mail@delete"); // Model: Delete
	$app->  post("mail/send", "Mail@send");   // Add E-mail to send queue
});