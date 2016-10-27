<?php
namespace App\Http\Controllers\V2;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\AccountingAccount;
use App\Traits\AccountingPeriod;

class EconomyReport extends Controller
{
	use AccountingPeriod;

	/**
	 *
	 */
	function valuationSheet(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
		$this->_getAccountingPeriodId($accountingperiod);

		// TODO: Hardcoded data
		$data = [
			"financial_year" => "2015-01-01 - 2015-12-31",
			"period" => [
				"from" => "2015-01-01",
				"to"   => "2015-12-31",
			],
			"created"       => date("Y-m-d H:i:s"),
			"last_instruction" => "A938",
			"children" => [
				[
					"title" => "Tillgångar",
					"children" => [
/*
						[
							"title" => "Anläggningstillgångar",
							"children" => [],
						],
*/
						[
							"title" => "Omsättningstillgångar",
							"children" => [
								[
									"title" => "Kortfristiga fordringar",
									"accountfilter" => [
										"from" => 1500,
										"to"   => 1599,
										"mul"  => 1,
									],
								],
								[
									"title" => "Kassa och bank",
									"accountfilter" => [
										"from" => 1900,
										"to"   => 1999,
										"mul"  => 1,
									],
								],
							],
						],
					],
				],
				[
					"title" => "Eget kapital, avsättningar och skulder",
					"children" => [
						[
							"title" => "Eget kapital",
							"accountfilter" => [
								"from" => 2000,
								"to"   => 2099,
								"mul"  => 1,
							],
						],
						[
							"title" => "Skulder",
							"accountfilter" => [
								"from" => 2400,
//								"to"   => 2499,
								"to"   => 2999,
								"mul"  => 1,
							],
						],
					]
				],
			],
		];

		return $this->_recursiveProcess($data);
	}

	/**
	 *
	 */
	function resultReport(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
		$this->_getAccountingPeriodId($accountingperiod);

		// TODO: Hardcoded data
		$data = [
			"financial_year" => "2015-01-01 - 2015-12-31",
			"period" => [
				"from" => "2015-01-01",
				"to"   => "2015-12-31",
			],
			"created"       => date("Y-m-d H:i:s"),
			"last_instruction" => "A938",
			"children" => [
				[
					"title" => "Rörelsens intäkter",
					"children" => [
						[
							"title" => "Nettoomsättning",
							"accountfilter" => [
								"from" => 3000,
								"to"   => 3299,
								"mul"  => -1,
							],
						],
						[
							"title" => "Aktiverat arbete för egen räkning",
							"accountfilter" => [
								"from" => 3800,
								"to"   => 3899,
								"mul"  => -1,
							],
						],
						[
							"title" => "Övriga rörelseintäkter",
							"accountfilter" => [
								"from" => 3900,
								"to"   => 3999,
								"mul"  => -1,
							],
						],
					],
				],
				[
					"title" => "Rörelsens kostnader",
					"children" => [
						[
							"title" => "Råvaror och förnödenheter",
							"accountfilter" => [
								"from" => 4000,
								"to"   => 4099,
								"mul"  => -1,
							],
						],
						[
							"title" => "Övriga externa kostnader",
							"accountfilter" => [
								"from" => 5000,
								"to"   => 6999,
								"mul"  => -1,
							],
						],
						[
							"title" => "Finansiella poster",
							"accountfilter" => [
								"from" => 8300,
								"to"   => 8399,
								"mul"  => -1,
							],
						],
					]
				],
				[
					"title" => "Rörelseresultat",
					"children" => [
						[
							"title" => "Årets resultat",
							"accountfilter" => [
								"from" => 8999,
								"to"   => 8999,
								"mul"  => 1,
							],
						],
					],
				],
			],
		];

		return $this->_recursiveProcess($data);
	}

	/**
	 *
	 */
	function _recursiveProcess($data)
	{
		$accountingperiod = 2015; // TODO: Hardcoded

		$data["balance_in"]     = 0;
		$data["balance_period"] = 0;
		$data["balance_out"]    = 0;

		if(array_key_exists("accountfilter", $data))
		{
			$accounts = AccountingAccount::list(
				[
					["accountingperiod", "=", $accountingperiod],
					["account_number", ">=", $data["accountfilter"]["from"]],
					["account_number", "<=", $data["accountfilter"]["to"]],
				]
			);

			foreach($accounts["data"] as &$account)
			{
				// Rename balance to balance_out
				$account->balance_out = $account->balance;
				unset($account->balance);

				// Calculate period
				$account->balance_period = $account->balance_out - $account->balance_in;

				// TODO: Olika konton reagerar olika på kredit / debet. Skall hämtas från kontoinställningar
				$account->balance_period *= $data["accountfilter"]["mul"];

				// Create sum
				$data["balance_in"]     += $account->balance_in;
				$data["balance_period"] += $account->balance_period;
				$data["balance_out"]    += $account->balance_out;
			}
			unset($account);

			$data["accounts"] = $accounts["data"];
		}

		if(!empty($data["children"]))
		{
			foreach($data["children"] as &$child)
			{
				$child = $this->_recursiveProcess($child);
				$data["balance_in"]     += $child["balance_in"];
				$data["balance_period"] += $child["balance_period"];
				$data["balance_out"]    += $child["balance_out"];
			}
			unset($child);
		}
		return $data;
	}
}