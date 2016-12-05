<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

// TODO: Remove
use App\Traits\Pagination;

class Costcenter extends Controller
{
	use Pagination;

	/**
	 *
	 */
	function list(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
		$x = $this->_getAccountingPeriodId($accountingperiod);

		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"entity" => [],
		], 201);
	}

	/**
	 *
	 */
	function create(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"entity" => [],
		], 201);
	}

	/**
	 *
	 */
	function read(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"entity" => [],
		], 201);
	}

	/**
	 *
	 */
	function update(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"entity" => [],
		], 201);
	}

	/**
	 *
	 */
	function delete(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"entity" => [],
		], 201);
	}
}