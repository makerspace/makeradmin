<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

//use App\Libraries\CurlBrowser;

class Recipient extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 * Return a list of all queued/sent messages
	 */
	function list(Request $request, $message_id)
	{
		// Paging filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
			"message_id" => $message_id,
		];

/*
		// Filter on relations
		if(!empty($request->get("relations")))
		{
			$filters["relations"] = $request->get("relations");
		}
*/

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
		$result = call_user_func("\App\Models\\Recipient::list", $filters);

		// Return json array
		return $result;
	}

	/**
	 * Return a list of all messages sent to a specific user
	 */
	function userlist(Request $request, $user_id)
	{
//		return $this->_applyStandardFilters("Message", $request);
		// Paging filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
			"member_id" => $user_id,
		];

/*
		// Filter on relations
		if(!empty($request->get("relations")))
		{
			$filters["relations"] = $request->get("relations");
		}
*/

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
		$result = call_user_func("\App\Models\\Recipient::list", $filters);

		// Return json array
		return $result;
	}
}