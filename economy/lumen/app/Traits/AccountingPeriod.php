<?php
namespace App\Traits;

use Illuminate\Http\Response;
use DB;

trait AccountingPeriod
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

class FilterNotFoundException extends \Exception
{
	protected $column;
	protected $data;

	function __construct($column, $data, $message)
	{
		$this->column = $column;
		$this->data = $data;
		$this->message = $message;
	}

	function getColumn()
	{
		return $this->column;
	}

	function getData()
	{
		return $this->data;
	}
}