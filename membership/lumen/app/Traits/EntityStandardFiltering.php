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

		// Load data from database
		$result = call_user_func("\App\Models\\{$model}::list", $filters);

		// Return json array
		return $result;
	}
}