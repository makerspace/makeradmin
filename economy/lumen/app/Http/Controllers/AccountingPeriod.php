<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

// Models
use App\Models\Period;

// TODO: Remove
use App\Traits\Pagination;

class AccountingPeriod extends Controller
{
	use Pagination;

	/**
	 *
	 */
	public function list(Request $request)
	{
		// Standard filters
		$filters = [
			"per_page" => $this->per_page($request),
		];

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

		// Load data from datbase
		$result = Period::list($filters);

		// Return json array
		return $result;
	}

	/**
	 *
	 */
	public function create(Request $request)
	{
		$json = $request->json()->all();

		// TODO: We need to check that the provided dates does not conflict with an existing period

		// Create new period
		$entity = new Period;
		$entity->title       = $json["title"]       ?? null;
//		$entity->description = $json["description"] ?? null;
		$entity->name        = $json["name"]        ?? null;
		$entity->start       = $json["start"]       ?? null;
		$entity->end         = $json["end"]         ?? null;

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "created",
			"data" => $entity->toArray(),
		], 201);
	}

	/**
	 *
	 */
	public function read(Request $request, $accountingperiod_id)
	{
		// Load the instruction entity
		$entity = Period::load([
			"accountingperiod_id" => $accountingperiod_id,
		]);

		// Generate an error if there is no such instruction
		if(false === $entity)
		{
			return Response()->json([
				"message" => "No period with specified id",
			], 404);
		}
		else
		{
			// Send response to client
			return Response()->json([
				"data" => $entity->toArray(),
			], 200);
		}
	}

	/**
	 *
	 */
	public function update(Request $request, $accountingperiod_id)
	{
//		return ['error' => 'not implemented'];
	}

	/**
	 * Delete an instruction
	 */
	public function delete(Request $request, $accountingperiod_id)
	{
		// Load the instruction entity
		$entity = Period::load([
			"accountingperiod_id" => $accountingperiod_id,
		]);

		// TODO: return Response()
		if($entity->delete())
		{
			return [
				"status" => "deleted"
			];
		}
		else
		{
			return [
				"status" => "error"
			];
		}
	}
}