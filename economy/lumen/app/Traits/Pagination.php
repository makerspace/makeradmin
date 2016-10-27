<?php

namespace App\Traits;
use Illuminate\Http\Request;

/**
 * This trait is used for doing uniform boundary checks on the per_page parameter used for pagination.
 *
 * Minimum value: 0
 * Maximum value: 1000
 * Default value: 25
 */
trait Pagination
{
	function per_page(Request $request)
	{
		// Use the specified per_page setting, if provided
		$per_page = $request->get("per_page");
		if(is_numeric($per_page) && $per_page > 1000)
		{
			$per_page = 1000;
		}
		else if(is_numeric($per_page) && $per_page > 0)
		{
			$per_page = (int)$per_page;
		}
		else
		{
			$per_page = 25;
		}

		return $per_page;
	}
}