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

$app->  post("membership/authenticate", "Member@authenticate");   // Authenticate a member

// Members
$app->   get("membership/member",      ['middleware' => 'permission:member_view',   'uses' => "Member@list"]);   // Get collection
$app->  post("membership/member",      ['middleware' => 'permission:member_create', 'uses' => "Member@create"]); // Model: Create
$app->   get("membership/member/{id}", ['middleware' => 'permission:member_view',   'uses' => "Member@read"]);   // Model: Read
$app->   put("membership/member/{id}", ['middleware' => 'permission:member_edit',   'uses' => "Member@update"]); // Model: Update
$app->delete("membership/member/{id}", ['middleware' => 'permission:member_delete', 'uses' => "Member@delete"]); // Model: Delete
$app->   get("membership/member/{id}/permissions",   ['middleware' => 'permission:permission_manage',   'uses' => "Member@getPermissions"]);    // Get a member's permissions
$app->   get("membership/member/{id}/groups",        ['middleware' => 'permission:group_member_view',   'uses' => "Member@getGroups"]);    // Get collection with members
$app->  post("membership/member/{id}/groups/add",    ['middleware' => 'permission:group_member_add',    'uses' => "Member@addGroup"]);    // Get collection with members
$app->  post("membership/member/{id}/groups/remove", ['middleware' => 'permission:group_member_remove', 'uses' => "Member@removeGroup"]);    // Get collection with members

// Groups
$app->   get("membership/group",       ['middleware' => 'permission:group_view',   'uses' => "Group@list"]);    // Get collection
$app->  post("membership/group",       ['middleware' => 'permission:group_create', 'uses' => "Group@create"]);  // Model: Create
$app->   get("membership/group/{id}",  ['middleware' => 'permission:group_view',   'uses' => "Group@read"]);    // Model: Read
$app->   put("membership/group/{id}",  ['middleware' => 'permission:group_edit',   'uses' => "Group@update"]);  // Model: Update
$app->delete("membership/group/{id}",  ['middleware' => 'permission:group_delete', 'uses' => "Group@delete"]);  // Model: Delete
$app->   get("membership/group/{id}/members", ['middleware' => 'permission:group_member_view',  'uses' => "Group@getMembers"]);    // Get collection with members

// Roles
$app->   get("membership/role",        "Role@list");     // Get collection
$app->  post("membership/role",        "Role@create");   // Model: Create
$app->   get("membership/role/{id}",   "Role@read");     // Model: Read
$app->   put("membership/role/{id}",   "Role@update");   // Model: Update
$app->delete("membership/role/{id}",   "Role@delete");   // Model: Delete

// Permissions
$app->   get("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@list"]);     // Get collection
$app->  post("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@create"]);   // Model: Create
$app->   get("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@read"]);     // Model: Read
$app->   put("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@update"]);   // Model: Update
$app->delete("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@delete"]);   // Model: Delete

$app->  post("membership/permission/register", "Permission@batchRegister");