<?php
namespace App\Traits;

trait EntityStandardFiltering
{
	/**
	 *
	 */
	protected function _applyStandardFilters($model, $request)
	{
		// Paging filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
		];

		// Filter on relations
		if(!empty($request->get("relations")))
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

		// Filter by id
		if(!empty($request->get("ids")))
		{
			$ids = explode(",", $request->get("ids"));
			$filters["ids"] = $ids;
		}

		// Load data from database
		$result = call_user_func("\App\Models\\{$model}::list", $filters);

		// Return json array
		return Response()->json($result, 201);
	}

	/**
	 * Generic delete function for entities
	 */
	protected function _delete($entity)
	{
		// Generate an error if there is no such entity
		if(false === $entity)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Could not find any entity with specified entity_id",
			], 404);
		}

		if($entity->delete())
		{
			return Response()->json([
				"status"  => "deleted",
				"message" => "The entity was successfully deleted",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "error",
				"message" => "An error occured when trying to delete entity",
			], 500);
		}
	}
}