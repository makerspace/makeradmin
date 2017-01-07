<?php

use Illuminate\Http\Response;
use Illuminate\Http\Request;

// TODO: Should only be included on OPTION requests?
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
header("Access-Control-Allow-Headers: Origin, Content-Type, Accept, Authorization, X-Request-With, Access-Control-Allow-Origin");
//header("Access-Control-Allow-Credentials: true");

// Tell client that this pre-flight info is valid for 20 days
header("Access-Control-Max-Age: 1728000");

// Index page, test to see if the user is logged in or not
$app->  get("/", "ServiceRegistry@test")->middleware("auth");

// OAuth 2.0 stuff
$app->  post("oauth/token",          "Authentication@login");
$app->  post("oauth/resetpassword",  "Authentication@reset");
$app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
$app->delete("oauth/token/{token}", ["middleware" => "auth", "uses" => "Authentication@logout"]);

// Service registry
$app->  post("service/register",   "ServiceRegistry@register");
$app->  post("service/unregister", "ServiceRegistry@unregister");
$app->   get("service/list",       "ServiceRegistry@list");

// Require an authenticated user for these requests
$app->group(["middleware" => "auth"], function() use ($app)
{
	// Relations
	$app->   get("relations", ["middleware" => "auth", "uses" => "Relations@relations"]);// TODO: Remove this API
	$app->   get("relation",  ["middleware" => "auth", "uses" => "Relations@relation"]);
	$app->  post("relation",  ["middleware" => "auth", "uses" => "Relations@createRelation"]);
	$app->   get("related",   ["middleware" => "auth", "uses" => "Relations@related"]);

	// Facades
	$app->   get("facade",    ["middleware" => "auth", "uses" => "Facade@index"]);

	// An ugly way to catch all request as lumen does not support the any() and match() methods used in Laravel
	$app->get("/{p1}",                        "ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}",                   "ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}/{p3}",              "ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}/{p3}/{p4}",         "ServiceRegistry@handleRoute");
	$app->get("/{p1}/{p2}/{p3}/{p4}/{p5}",    "ServiceRegistry@handleRoute");
	$app->put("/{p1}",                        "ServiceRegistry@handleRoute");
	$app->put("/{p1}/{p2}",                   "ServiceRegistry@handleRoute");
	$app->put("/{p1}/{p2}/{p3}",              "ServiceRegistry@handleRoute");
	$app->put("/{p1}/{p2}/{p3}/{p4}",         "ServiceRegistry@handleRoute");
	$app->put("/{p1}/{p2}/{p3}/{p4}/{p5}",    "ServiceRegistry@handleRoute");
	$app->post("/{p1}",                       "ServiceRegistry@handleRoute");
	$app->post("/{p1}/{p2}",                  "ServiceRegistry@handleRoute");
	$app->post("/{p1}/{p2}/{p3}",             "ServiceRegistry@handleRoute");
	$app->post("/{p1}/{p2}/{p3}/{p4}",        "ServiceRegistry@handleRoute");
	$app->post("/{p1}/{p2}/{p3}/{p4}/{p5}",   "ServiceRegistry@handleRoute");
	$app->delete("/{p1}",                     "ServiceRegistry@handleRoute");
	$app->delete("/{p1}/{p2}",                "ServiceRegistry@handleRoute");
	$app->delete("/{p1}/{p2}/{p3}",           "ServiceRegistry@handleRoute");
	$app->delete("/{p1}/{p2}/{p3}/{p4}",      "ServiceRegistry@handleRoute");
	$app->delete("/{p1}/{p2}/{p3}/{p4}/{p5}", "ServiceRegistry@handleRoute");
});

// Handle CORS requests
$app->options("/",                         "ServiceRegistry@handleOptions");
$app->options("/{p1}",                     "ServiceRegistry@handleOptions");
$app->options("/{p1}/{p2}",                "ServiceRegistry@handleOptions");
$app->options("/{p1}/{p2}/{p3}",           "ServiceRegistry@handleOptions");
$app->options("/{p1}/{p2}/{p3}/{p4}",      "ServiceRegistry@handleOptions");
$app->options("/{p1}/{p2}/{p3}/{p4}/{p5}", "ServiceRegistry@handleOptions");