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
	$app->   get("accountingperiod",      "AccountingPeriod@list");   // Get collection
	$app->  post("accountingperiod",      "AccountingPeriod@create"); // Model: Create
	$app->   get("accountingperiod/{id}", "AccountingPeriod@read");   // Model: Read
	$app->   put("accountingperiod/{id}", "AccountingPeriod@update"); // Model: Update
	$app->delete("accountingperiod/{id}", "AccountingPeriod@delete"); // Model: Delete

	// Get a list of transactions independent of accounting period
	$app->   get("transactions", "Transactions@transactions");   // Get collection
});

$app->group(array("prefix" => "economy/{accountingperiod}"), function() use ($app)
{
	// Accounts
	$app->   get("account",          "Account@list");        // Get collection
	$app->  post("account",          "Account@create");      // Model: Create
	$app->   get("account/{id}/transactions", "Account@transactions"); // Transactions collection
	$app->   get("account/{id}",     "Account@read");        // Model: Read
	$app->   put("account/{id}",     "Account@update");      // Model: Update
	$app->delete("account/{id}",     "Account@delete");      // Model: Delete

	// Instructions
	$app->   get("instruction",      "Instruction@list");    // Get collection
	$app->  post("instruction",      "Instruction@create");  // Model: Create
	$app->   get("instruction/{id}", "Instruction@read");    // Model: Read
	$app->   put("instruction/{id}", "Instruction@update");  // Model: Update
	$app->delete("instruction/{id}", "Instruction@delete");  // Model: Delete

	// Transactions
	$app->   get("transaction",      "Transactions@list");   // Get collection
	$app->  post("transaction",      "Transactions@create"); // Model: Create
	$app->   get("transaction/{id}", "Transactions@read");   // Model: Read
	$app->   put("transaction/{id}", "Transactions@update"); // Model: Update
	$app->delete("transaction/{id}", "Transactions@delete"); // Model: Delete

	// Cost centers
	$app->   get("costcenter",       "Costcenter@list");     // Get collection
	$app->  post("costcenter",       "Costcenter@create");   // Model: Create
	$app->   get("costcenter/{id}",  "Costcenter@read");     // Model: Read
	$app->   put("costcenter/{id}",  "Costcenter@update");   // Model: Update
	$app->delete("costcenter/{id}",  "Costcenter@delete");   // Model: Delete

	// Master ledger
	$app->   get("masterledger",     "Account@masterledger");  // Get collection

	// Reports
	$app->   get("valuationsheet",   "Report@valuationSheet"); // Get collection
	$app->   get("resultreport",     "Report@resultReport");   // Get collection

	// Files / vouchers
	$app->   get("file/{external_id}/{filename}", "Economy@file"); // Get collection

	// Maintenance / Debugging
	$app->get("debug/updateinstructionnumbers", "Maintenance@updateInstructionNumbers");
	$app->get("debug/unbalanced",               "Maintenance@unbalancedInstructions");
});