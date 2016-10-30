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

use Illuminate\Http\Response;
use Illuminate\Http\Request;

use \App\Http\Controllers\ServiceRegistry;

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
header("Access-Control-Allow-Headers: Origin, Content-Type, Accept, Authorization, X-Request-With, Access-Control-Allow-Origin");
//header("Access-Control-Allow-Credentials: true");

// API version 2
$app->group(["prefix" => "v1"], function() use ($app)
{
	// TODO: Return information about software version, etc
	$app->get("/version", function() use ($app)
	{
		return Response()->json([
			"version" => $app->version()
		], 200);
	});

	// Service registry
	$app->  post("service/register",       "ServiceRegistry@register");
	$app->  post("service/unregister",     "ServiceRegistry@unregister");
	$app->   get("service/list",           "ServiceRegistry@list");

	// Test to see if the user is logged in or not
	$app->get("/test", function () use ($app)
	{
		$user = Auth::user();
		if(!$user)
		{
			return Response()->json([
				"status"  => "ok",
				"message" => "Hello not logged in user!",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "ok",
				"message" => "Hello user {$user->user_id}!",
			], 200);
		}
	});

	// An ugly way to catch all request as lumen does not support the any() and match() methods used in Laravel
	$app->get("/{p1}",                "\App\Http\Controllers\ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}",           "\App\Http\Controllers\ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}/{p3}",      "\App\Http\Controllers\ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}/{p3}/{p4}", "\App\Http\Controllers\ServiceRegistry@handleRoute");

	// Handle CORS requests
	$app->options("/",                    "\App\Http\Controllers\ServiceRegistry@handleOptions");
	$app->options("/{p1}",                "\App\Http\Controllers\ServiceRegistry@handleOptions");
	$app->options("/{p1}/{p2}",           "\App\Http\Controllers\ServiceRegistry@handleOptions");
	$app->options("/{p1}/{p2}/{p3}",      "\App\Http\Controllers\ServiceRegistry@handleOptions");
	$app->options("/{p1}/{p2}/{p3}/{p4}", "\App\Http\Controllers\ServiceRegistry@handleOptions");
});