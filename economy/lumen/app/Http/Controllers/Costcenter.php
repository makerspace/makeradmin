<?php
namespace App\Http\Controllers;

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
	public function list(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
		$x = $this->_getAccountingPeriodId($accountingperiod);

		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"data" => [],
		], 201);
	}

	/**
	 *
	 */
	public function create(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"data" => [],
		], 201);
	}

	/**
	 *
	 */
	public function read(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"data" => [],
		], 201);
	}

	/**
	 *
	 */
	public function update(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"data" => [],
		], 201);
	}

	/**
	 *
	 */
	public function delete(Request $request, $accountingperiod, $id)
	{
		// Send response to client
		return Response()->json([
			"status" => "not_implemented",
			"data" => [],
		], 201);
	}
}