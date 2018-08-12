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
	// MultiAccess
	$app->   get("multiaccess/file/{filename}", ['middleware' => 'permission:sync_view', 'uses' => "MultiAccessSync@diff"]);
	$app->  post("multiaccess/upload",          ['middleware' => 'permission:sync_view', 'uses' => "MultiAccessSync@upload"]);

	// External data fetch.
	$app->   get("multiaccess/memberdata",      ['middleware' => 'permission:sync_service_external', 'uses' => "MultiAccessSync@dumpmembers"]);
});
