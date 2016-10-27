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

// Members
$app->   get("membership/member",      "Member@list");   // Get collection
$app->  post("membership/member",      "Member@create"); // Model: Create
$app->   get("membership/member/{id}", "Member@read");   // Model: Read
$app->   put("membership/member/{id}", "Member@update"); // Model: Update
$app->delete("membership/member/{id}", "Member@delete"); // Model: Delete

// Groups
$app->   get("membership/group",       "Group@list");    // Get collection
$app->  post("membership/group",       "Group@create");  // Model: Create
$app->   get("membership/group/{id}",  "Group@read");    // Model: Read
$app->   put("membership/group/{id}",  "Group@update");  // Model: Update
$app->delete("membership/group/{id}",  "Group@delete");  // Model: Delete

// Roles
$app->   get("membership/role",        "Role@list");     // Get collection
$app->  post("membership/role",        "Role@create");   // Model: Create
$app->   get("membership/role/{id}",   "Role@read");     // Model: Read
$app->   put("membership/role/{id}",   "Role@update");   // Model: Update
$app->delete("membership/role/{id}",   "Role@delete");   // Model: Delete

// Permissions
$app->   get("membership/permission",        "Permission@list");     // Get collection
$app->  post("membership/permission",        "Permission@create");   // Model: Create
$app->   get("membership/permission/{id}",   "Permission@read");     // Model: Read
$app->   put("membership/permission/{id}",   "Permission@update");   // Model: Update
$app->delete("membership/permission/{id}",   "Permission@delete");   // Model: Delete
