<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

// Models
use App\Models\Transaction;

// TODO: Remove
use App\Traits\Pagination;

class Transactions extends Controller
{
	use Pagination;

	/**
	 *
	 */
	function list(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
//		$accountingperiod_id = $this->_getAccountingPeriodId($accountingperiod);

		// Paging filter
		$filters = [
			"per_page" => $this->per_page($request),
//			"account_number" => $account_number,
//			"accountingperiod" => $accountingperiod,
		];

		// Filter on relations
		if($request->get("relations"))
		{
			$filters["relations"] = $request->get("relations");
		}

		// Filter on search
		if(!empty($request->get("search")))
		{
			$filters["search"] = $request->get("search");
		}

		// Sorting
		if(!empty($request->get("sort_by")))
		{
			$order = ($request->get("sort_order") == "desc" ? "desc" : "asc");
			$filters["sort"] = [$request->get("sort_by"), $order];
		}

		// Filters
		if(!empty($request->get("account_number")))
		{
			$filters["account_number"] = ["=", $request->get("account_number")];
		}

		// Load data from database
		$result = Transaction::list($filters);

		// Return json array
		return $result;
	}

	/**
	 *
	 */
	function create(Request $request, $accountingperiod)
	{
		return ['error' => 'not implemented'];
	}

	/**
	 *
	 */
	function read(Request $request, $accountingperiod, $account_number)
	{
		// Check that the specified accounting period exists
		$accountingperiod_id = $this->_getAccountingPeriodId($accountingperiod);

		$result = Transaction::list(
			[
				["per_page", $this->per_page($request)],
				["account_number", "=", $account_number],
				["accountingperiod", "=", $accountingperiod],
			]
		);

		// Generate an error if there is no such instruction
		if(count($result["data"]) == 0)
		{
			return Response()->json([
				"message" => "No transactions found",
			], 404);
		}
		else
		{
			// Return json array
			return $result;
			// Send response to client
			return Response()->json([
				"data" => $result->toArray(),
			], 200);
		}
	}

	/**
	 *
	 */
	function update(Request $request, $accountingperiod, $id)
	{
		return ['error' => 'not implemented'];
	}

	/**
	 *
	 */
	function delete(Request $request, $accountingperiod, $id)
	{
		return ['error' => 'not implemented'];
	}
}