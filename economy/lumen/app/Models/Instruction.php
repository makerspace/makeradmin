<?php
namespace App\Models;

use App\Models\Entity;
use App\Models\Transaction;
use DB;

/**
 *
 */
class Instruction extends Entity
{
	protected $type = "instruction";
	protected $table = "economy_instruction";
	protected $id_column = "instruction_id";
	protected $columns = [
		"instruction_id" => [
			"column" => "economy_instruction.economy_instruction_id",
			"select" => "economy_instruction.economy_instruction_id",
		],
		"created_at" => [
			"column" => "economy_instruction.created_at",
			"select" => "DATE_FORMAT(economy_instruction.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "economy_instruction.updated_at",
			"select" => "DATE_FORMAT(economy_instruction.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "economy_instruction.title",
			"select" => "economy_instruction.title",
		],
		"description" => [
			"column" => "economy_instruction.description",
			"select" => "economy_instruction.description",
		],
		"instruction_number" => [
			"column" => "economy_instruction.instruction_number",
			"select" => "economy_instruction.instruction_number",
		],
		"accounting_date" => [
			"column" => "economy_instruction.accounting_date",
			"select" => "DATE_FORMAT(economy_instruction.accounting_date, '%Y-%m-%d')",
		],
		"economy_category" => [
			"column" => "economy_instruction.economy_category_id",
			"select" => "economy_instruction.economy_category_id",
		],
		"importer" => [
			"column" => "economy_instruction.importer",
			"select" => "economy_instruction.importer",
		],
		"external_id" => [
			"column" => "economy_instruction.external_id",
			"select" => "economy_instruction.external_id",
		],
		"external_date" => [
			"column" => "economy_instruction.external_date",
			"select" => "economy_instruction.external_date",
		],
		"external_text" => [
			"column" => "economy_instruction.external_text",
			"select" => "economy_instruction.external_text",
		],
		"external_data" => [
			"column" => "economy_instruction.external_data",
			"select" => "economy_instruction.external_data",
		],
		"verificationseries_id" => [
			"column" => "economy_instruction.economy_verificationseries_id",
			"select" => "economy_instruction.economy_verificationseries_id",
		],
		"accountingperiod_id" => [
			"column" => "economy_instruction.economy_accountingperiod_id",
			"select" => "economy_instruction.economy_accountingperiod_id",
		],
	];
	protected $sort = ["instruction_number", "desc"];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
					->  where("economy_instruction.title",              "like", "%".$word."%")
					->orWhere("economy_instruction.description",        "like", "%".$word."%")
					->orWhere("economy_instruction.instruction_number", "like", "%".$word."%")
					->orWhere("economy_instruction.external_id",        "like", "%".$word."%");
			});
		}

		return $query;
	}

	/**
	 *
	 */
	public function _list($filters = [])
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery();

		// Go through filters
		foreach($filters as $id => $filter)
		{
			if(is_array($filter) && count($filter) >= 2)
			{
				$op    = $filter[0];
				$param = $filter[1];
			}
			else
			{
				$op    = "=";
				$param = $filter;
			}

			// Filter on accounting period
			if("accountingperiod" == $id)
			{
				$query = $query
					->leftJoin("economy_accountingperiod", "economy_accountingperiod.economy_accountingperiod_id", "=", "economy_instruction.economy_accountingperiod_id")
					->where("economy_accountingperiod.name", $op, $param);
				unset($filters[$id]);
			}
			// Filter on transaction.economy_account_id
			else if("account_id" == $id)
			{
				$query = $query
					->join("economy_transaction", "economy_transaction.economy_instruction_id", "=", "economy_instruction.economy_instruction_id")
					->join("economy_account", "economy_account.economy_account_id", "=", "economy_transaction.economy_account")
					->where("economy_account.account_number", $op, $param);
				unset($filters[$id]);
			}
			else if("has_voucher" == $id)
			{
				$filter_vouchers = $filter;
				unset($filters[$id]);
			}
			// Pagination
			else if("per_page" == $id)
			{
				$this->pagination = $filter;
				unset($filters[$id]);
			}
		}

		// Apply standard filters like id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Get the balance
		$query->selectRaw("(SELECT SUM(amount) FROM economy_transaction WHERE amount > 0 AND economy_instruction_id = economy_instruction.economy_instruction_id) AS balance");

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$result = $query->get();

		// Indicate if the instruction has attached vouchers or not
		$data = [];
		foreach($result as $id => $row)
		{
//			// Append files ("Verifikat")
//			$row->files = [];
			$row->has_vouchers = false;
			if(!empty($row->external_id))
			{
				$dir = "/var/www/html/vouchers/{$row->external_id}";
				if(file_exists($dir))
				{
					$row->has_vouchers = true;
/*
					foreach(glob("{$dir}/*") as $file)
					{
						$row["files"][] = basename($file);
					}
*/
				}
			}

			// Apply filter: Remove all instructions with a voucher
			if(!(isset($filter_vouchers) && $filter_vouchers === true && $row->has_vouchers === true))
			{
				$data[] = $row;
			}
		}

		// If we removed rows in the foreach above the indexing will be wrong, so we need to remove all keys.
		$result = [
			"data" => $data
		];

		if($this->pagination != null)
		{
			$result["total"]     = $query->getCountForPagination();
			$result["per_page"]  = $this->pagination;
			$result["last_page"] = ceil($result["total"] / $result["per_page"]);
		}

		return $result;
	}

	/*
	 * Same as above, but called non-statically
	 */
	public function _load($filters, $show_deleted = false)
	{
		// Load accounting instruction
		$query = $this->_buildLoadQuery();

		// Go through filters
		foreach($filters as $id => $filter)
		{
			if(is_array($filter) && count($filter) >= 2)
			{
				$op    = $filter[0];
				$param = $filter[1];
			}
			else
			{
				$op    = "=";
				$param = $filter;
			}

			// Filter on accounting period
			if("accountingperiod" == $id)
			{
				$query = $query
					->leftJoin("economy_accountingperiod", "economy_accountingperiod.economy_accountingperiod_id", "=", "economy_instruction.economy_accountingperiod_id")
					->where("economy_accountingperiod.name", $op, $param);
				unset($filters[$id]);
			}
			else if("instruction_number" == $id)
			{
				// Filter on instruction_number
				$query = $query->where("economy_instruction.instruction_number", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Join transactions table and calculate balance
		$query = $query
			->leftJoin("economy_transaction", "economy_transaction.economy_instruction_id", "=", "economy_instruction.economy_instruction_id")
			->groupBy("economy_instruction.economy_instruction_id")
			->where("economy_transaction.amount", ">", 0)
			->selectRaw("SUM(amount) AS balance");

		// Get result from database
		$data = (array)$query->first();

		// Generate an error if there is no such instruction
		if(empty($data))
		{
			return false;
		}

		// Create a new entity
		$entity = new Instruction;

		// The columns is fetched with an "column AS name", so no need to translate the $column_id
		$entity->entity_id = $data[$this->id_column];

		// Populate the entity with data
		foreach($data as $key => $value)
		{
			$entity->{$key} = $value;
		}

		// Load the transactions
		$entity->transactions = DB::table("economy_instruction")
			->join("economy_transaction", "economy_transaction.economy_instruction_id", "=", "economy_instruction.economy_instruction_id")
			->join("economy_account", "economy_transaction.economy_account_id", "=", "economy_account.economy_account_id")
			->where("economy_instruction.economy_instruction_id", "=", $entity->instruction_id)
			->select(
				"economy_transaction.economy_transaction_id AS transaction_id",
				"economy_instruction.title",
				"economy_instruction.description",
				"economy_transaction.amount AS balance",
				"economy_account.account_number",
				"economy_account.title AS account_title"
			)
			->get();

		// Return the entity
		return $entity;
	}

	/**
	 *
	 */
	public function save()
	{
		$result = parent::save();

		if(!$this->entity_id)
		{
			die("Error: No id\n");
		}

		// Insert posts
		if(!empty($this->data["transactions"]))
		{
			foreach($this->data["transactions"] as $i => $transaction)
			{
				$entity = new Transaction;
				$entity->instruction_id = $this->entity_id;
				$entity->title          = $transaction["title"];
				$entity->account_id     = $this->_getAccountEntityId($this->data["accountingperiod_id"], $transaction["account_number"]);
				$entity->amount         = $transaction["amount"];
				$entity->costcenter_id  = $transaction["economy_cost_center"] ?? null;
				$entity->external_id    = $transaction["external_id"] ?? null;

				// Add relations
				if(!empty($transaction["relations"]))
				{
					$entity->addRelations($transaction["relations"]);
				}

				// Save the entity
				$entity->save();
			}
		}

		return $result;
	}

	protected function _getAccountEntityId($accountingperiod_id, $account_number)
	{
		return DB::table("economy_account")
//			->leftJoin("economy_accountingperiod", "economy_accountingperiod.economy_accountingperiod_id", "=", "economy_account.economy_accountingperiod_id")
			->where("account_number", $account_number)
//			->where("economy_accountingperiod.name", $accountingperiod)
			->where("economy_accountingperiod_id", $accountingperiod_id)
			->value("economy_account_id");
	}
}