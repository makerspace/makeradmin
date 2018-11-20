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
$app->  get("/", ["middleware" => "auth:service", "uses" => "ServiceRegistry@test"]);

// OAuth 2.0 stuff
$app->  post("oauth/token",          "Authentication@login");
$app->  post("oauth/resetpassword",  "Authentication@reset");
$app->   get("oauth/token",         ["middleware" => "auth", "uses" => "Authentication@listTokens"]);
$app->delete("oauth/token/{token}", ["middleware" => "auth", "uses" => "Authentication@logout"]);

// Allow other services to get login tokens for any user
$app->  post("oauth/force_token", ["middleware" => "auth:service", "uses" => "Authentication@unauthenticated_login"]);

// Some unauthenticated requests
// TODO: Can this be handled in a nicer way?
$app->post("member/send_access_token", "ServiceRegistry@handleRoute");
$app->post("webshop/register", "ServiceRegistry@handleRoute");
$app->post("webshop/stripe_callback", "Webhooks@stripe");
$app->get("webshop/product_data", "ServiceRegistry@handleRoute");
$app->get("webshop/product_data/{id}", "ServiceRegistry@handleRoute");

$app->get("webshop/product_data",      "ServiceRegistry@handleRoute");
$app->get("webshop/product_data/{p3}", "ServiceRegistry@handleRoute");

// Service registry
$app->post("service/register",   ["middleware" => "auth:service", "uses" => "ServiceRegistry@register"]);
$app->post("service/unregister", ["middleware" => "auth:service", "uses" => "ServiceRegistry@unregister"]);

// Require an authenticated user for these requests
$app->group(["middleware" => "auth"], function() use ($app)
{
	// Service registry
	$app->   get("service/list", ["middleware" => "permission:service", "uses" => "ServiceRegistry@list"]);

	// Relations
	$app->   get("relations",    ["middleware" => "permission:member_view", "uses" => "Relations@relations"]);// TODO: Remove this API
	$app->   get("relation",     ["middleware" => "permission:member_view", "uses" => "Relations@relation"]);
	$app->  post("relation",     ["middleware" => "permission:member_view", "uses" => "Relations@createRelation"]);
	$app->   get("related",      ["middleware" => "permission:member_view", "uses" => "Relations@related"]);

	// Facades
	$app->   get("facade",    "Facade@index");

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
