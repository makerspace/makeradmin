<?php
namespace App\Http\Controllers\V2;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\AccountingInstruction;
use App\Traits\AccountingPeriod;
use App\Traits\Pagination;

class EconomyInstruction extends Controller
{
	use AccountingPeriod, Pagination;

	/**
	 *
	 */
	function list(Request $request, $accountingperiod)
	{
		// Check that the specified accounting period exists
		$this->_getAccountingPeriodId($accountingperiod);

		// Standard filters
		$filters = [
			"per_page" => $this->per_page($request),
			"accountingperiod" => ["=", $accountingperiod],
//			"has_voucher" => ["=", true],
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
		$result = AccountingInstruction::list($filters);

		// Return json array
		return $result;
	}

	/**
	 *
	 */
	function create(Request $request, $accountingperiod)
	{
		$json = $request->json()->all();

		// Get id of accounting period
		$accountingperiod_id = $this->_getAccountingPeriodId($accountingperiod);

		// We need to check that the provided account number is not in conflict with an existing one
/*
		if($this->_accountNumberIsExisting($json["account_number"]))
		{
			return Response()->json([
				"message" => "The specified account number does already exist",
			], 404); // TODO: Another error code
		}
*/
		// Create new accounting instruction
		$entity = new AccountingInstruction;
		$entity->title                         = $json["title"];
		$entity->description                   = $json["description"]         ?? null;
		$entity->instruction_number            = $json["instruction_number"]  ?? null;
		$entity->accounting_date               = $json["accounting_date"];
		$entity->accounting_category           = $json["accounting_category"] ?? null;
		$entity->importer                      = $json["importer"]            ?? null;
		$entity->external_id                   = $json["external_id"]         ?? null;
		$entity->external_date                 = $json["external_date"]       ?? null;
		$entity->external_text                 = $json["external_text"]       ?? null;
		/*
		$entity->external_data                 = $json["external_data"]       ?? null;
		*/
		$entity->accounting_verification_serie = $json["accounting_verification_serie"] ?? null;
		$entity->transactions                  = $json["transactions"];
		$entity->accounting_period             = $accountingperiod_id;

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "created",
			"entity" => $entity->toArray(),
		], 201);
	}

	/**
	 *
	 */
	function read(Request $request, $accountingperiod, $instruction_number)
	{
		// Check that the specified accounting period exists, or throw an FilterNotFoundException
		$this->_getAccountingPeriodId($accountingperiod);

		// Load the instruction entity
		$entity = AccountingInstruction::load([
			"accountingperiod"   => $accountingperiod,
			"instruction_number" => $instruction_number,
		]);

		// Generate an error if there is no such instruction
		if(false === $entity)
		{
			return Response()->json([
				"message" => "No instruction with specified instruction number",
			], 404);
		}
		else
		{
			// Append files ("Verifikat")
			$files = [];
			if(!empty($entity->external_id))
			{
				$dir = "/var/www/html/vouchers/{$entity->external_id}";
				if(file_exists($dir))
				{
					foreach(glob("{$dir}/*") as $file)
					{
						$files[] = basename($file);
					}
				}
			}
			$entity->files = $files;

			return $entity->toArray();
		}
	}

	/**
	 *
	 */
	function update(Request $request, $accountingperiod, $id)
	{
		return ['error' => 'not implemented'];
	}

	/**
	 * Delete an instruction
	 */
	function delete(Request $request, $accountingperiod, $instruction_number)
	{
		// Check that the specified accounting period exists, or throw an FilterNotFoundException
		$this->_getAccountingPeriodId($accountingperiod);

		// Load the instruction entity
		$entity = AccountingInstruction::load([
			"accountingperiod"   => $accountingperiod,
			"instruction_number" => $instruction_number,
		]);

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