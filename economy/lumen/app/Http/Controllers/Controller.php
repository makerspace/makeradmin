<?php

namespace App\Http\Controllers;

use Laravel\Lumen\Routing\Controller as BaseController;
use App\Exceptions\FilterNotFoundException;
use DB;

class Controller extends BaseController
{
	/**
	 * Get the entity_id of the specified accounting period
	 */
	protected function _getAccountingPeriodId($period)
	{
		$accountingperiod_id = DB::table("accounting_period")
			->where("name", "=", $period)
			->value("entity_id");

		if(null === $accountingperiod_id)
		{
			throw new FilterNotFoundException("accountingperiod", $period, "Could not find the specified accounting period");
		}

		return $accountingperiod_id;
	}
}
