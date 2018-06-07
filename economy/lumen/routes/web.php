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

// Economy
$app->group(array("prefix" => "economy"), function() use ($app)
{
	// Accounting periods
	$app->   get("accountingperiod",      ['middleware' => 'permission:economy_view',  'uses' => "AccountingPeriod@list"]);   // Get collection
	$app->  post("accountingperiod",      ['middleware' => 'permission:economy_edit',  'uses' => "AccountingPeriod@create"]); // Model: Create
	$app->   get("accountingperiod/{id}", ['middleware' => 'permission:economy_view',  'uses' => "AccountingPeriod@read"]);   // Model: Read
	$app->   put("accountingperiod/{id}", ['middleware' => 'permission:economy_edit',  'uses' => "AccountingPeriod@update"]); // Model: Update
	$app->delete("accountingperiod/{id}", ['middleware' => 'permission:economy_admin', 'uses' => "AccountingPeriod@delete"]); // Model: Delete

	// Get a list of transactions independent of accounting period
	$app->   get("transactions", ['middleware' => 'permission:transaction_view', 'uses' => "Transactions@transactions"]);   // Get collection
});

$app->group(array("prefix" => "economy/{accountingperiod}"), function() use ($app)
{
	// Accounts
	$app->   get("account",          ['middleware' => 'permission:economy_view',  'uses' => "Account@list"]);        // Get collection
	$app->  post("account",          ['middleware' => 'permission:economy_edit',  'uses' => "Account@create"]);      // Model: Create
	$app->   get("account/{id}/transactions", ['middleware' => 'permission:economy_view', 'uses' => "Account@transactions"]); // Transactions collection
	$app->   get("account/{id}",     ['middleware' => 'permission:economy_view',  'uses' => "Account@read"]);        // Model: Read
	$app->   put("account/{id}",     ['middleware' => 'permission:economy_edit',  'uses' => "Account@update"]);      // Model: Update
	$app->delete("account/{id}",     ['middleware' => 'permission:economy_admin', 'uses' => "Account@delete"]);      // Model: Delete

	// Instructions
	$app->   get("instruction",      ['middleware' => 'permission:economy_view',  'uses' => "Instruction@list"]);    // Get collection
	$app->  post("instruction",      ['middleware' => 'permission:economy_edit',  'uses' => "Instruction@create"]);  // Model: Create
	$app->   get("instruction/{id}", ['middleware' => 'permission:economy_view',  'uses' => "Instruction@read"]);    // Model: Read
	$app->   put("instruction/{id}", ['middleware' => 'permission:economy_edit',  'uses' => "Instruction@update"]);  // Model: Update
	$app->delete("instruction/{id}", ['middleware' => 'permission:economy_admin', 'uses' => "Instruction@delete"]);  // Model: Delete

	// Transactions
	$app->   get("transaction",      ['middleware' => 'permission:economy_view',  'uses' => "Transactions@list"]);   // Get collection
	$app->  post("transaction",      ['middleware' => 'permission:economy_edit',  'uses' => "Transactions@create"]); // Model: Create
	$app->   get("transaction/{id}", ['middleware' => 'permission:economy_view',  'uses' => "Transactions@read"]);   // Model: Read
	$app->   put("transaction/{id}", ['middleware' => 'permission:economy_edit',  'uses' => "Transactions@update"]); // Model: Update
	$app->delete("transaction/{id}", ['middleware' => 'permission:economy_admin', 'uses' => "Transactions@delete"]); // Model: Delete

	// Cost centers
	$app->   get("costcenter",       ['middleware' => 'permission:economy_view',  'uses' => "Costcenter@list"]);     // Get collection
	$app->  post("costcenter",       ['middleware' => 'permission:economy_edit',  'uses' => "Costcenter@create"]);   // Model: Create
	$app->   get("costcenter/{id}",  ['middleware' => 'permission:economy_view',  'uses' => "Costcenter@read"]);     // Model: Read
	$app->   put("costcenter/{id}",  ['middleware' => 'permission:economy_edit',  'uses' => "Costcenter@update"]);   // Model: Update
	$app->delete("costcenter/{id}",  ['middleware' => 'permission:economy_admin', 'uses' => "Costcenter@delete"]);   // Model: Delete

	// Master ledger
	$app->   get("masterledger",     ['middleware' => 'permission:economy_view',  'uses' => "Account@masterledger"]);  // Get collection

	// Reports
	$app->   get("valuationsheet",   ['middleware' => 'permission:result_view',   'uses' => "Report@valuationSheet"]); // Get collection
	$app->   get("resultreport",     ['middleware' => 'permission:result_view',   'uses' => "Report@resultReport"]);   // Get collection

	// Files / vouchers
	$app->   get("file/{external_id}/{filename}", ['middleware' => 'permission:economy_view', 'uses' => "Economy@file"]); // Get collection

	// Maintenance / Debugging
	$app->get("debug/updateinstructionnumbers", ['middleware' => 'permission:economy_view', 'uses' => "Maintenance@updateInstructionNumbers"]);
	$app->get("debug/unbalanced",               ['middleware' => 'permission:economy_view', 'uses' => "Maintenance@unbalancedInstructions"]);
});