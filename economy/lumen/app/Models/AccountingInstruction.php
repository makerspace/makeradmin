<?php
namespace App\Models;

use App\Models\Entity;
use App\Models\AccountingTransaction;
use DB;

/*
TODO

public function Transactions()
{
	return $this->hasMany('App\Models\AccountingTransaction');
}
*/


/**
 *
 */
class AccountingInstruction extends Entity
{
	protected $type = "accounting_instruction";
	protected $join = "accounting_instruction";
	protected $columns = [
		"entity_id" => [
			"column" => "entity.entity_id",
			"select" => "entity.entity_id",
		],
		"created_at" => [
			"column" => "entity.created_at",
			"select" => "DATE_FORMAT(entity.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "entity.updated_at",
			"select" => "DATE_FORMAT(entity.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "entity.title",
			"select" => "entity.title",
		],
		"description" => [
			"column" => "entity.description",
			"select" => "entity.description",
		],
		"instruction_number" => [
			"column" => "accounting_instruction.instruction_number",
			"select" => "accounting_instruction.instruction_number",
		],
		"accounting_date" => [
			"column" => "accounting_instruction.accounting_date",
			"select" => "accounting_instruction.accounting_date",
		],
		"accounting_category" => [
			"column" => "accounting_instruction.accounting_category",
			"select" => "accounting_instruction.accounting_category",
		],
		"importer" => [
			"column" => "accounting_instruction.importer",
			"select" => "accounting_instruction.importer",
		],
		"external_id" => [
			"column" => "accounting_instruction.external_id",
			"select" => "accounting_instruction.external_id",
		],
		"external_date" => [
			"column" => "accounting_instruction.external_date",
			"select" => "accounting_instruction.external_date",
		],
		"external_text" => [
			"column" => "accounting_instruction.external_text",
			"select" => "accounting_instruction.external_text",
		],
		"external_data" => [
			"column" => "accounting_instruction.external_data",
			"select" => "accounting_instruction.external_data",
		],
		"accounting_verification_series" => [
			"column" => "accounting_instruction.accounting_verification_series",
			"select" => "accounting_instruction.accounting_verification_series",
		],
		"accounting_period" => [
			"column" => "accounting_instruction.accounting_period",
			"select" => "accounting_instruction.accounting_period",
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
					->  where("entity.title",                              "like", "%".$word."%")
					->orWhere("entity.description",                        "like", "%".$word."%")
					->orWhere("accounting_instruction.instruction_number", "like", "%".$word."%")
					->orWhere("accounting_instruction.external_id",        "like", "%".$word."%");
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
					->leftJoin("accounting_period", "accounting_period.entity_id", "=", "accounting_instruction.accounting_period")
					->where("accounting_period.name", $op, $param);
				unset($filters[$id]);
			}
			// Filter on transaction.account_id
			else if("account_id" == $id)
			{
				$query = $query
					->join("accounting_transaction", "accounting_transaction.accounting_instruction", "=", "entity.entity_id")
					->join("accounting_account", "accounting_account.entity_id", "=", "accounting_transaction.accounting_account")
					->where("accounting_account.account_number", $op, $param);
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

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Get the balance
		$query->selectRaw("(SELECT SUM(amount) FROM accounting_transaction WHERE amount > 0 AND accounting_instruction = entity.entity_id) AS balance");

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$data = $query->get();

		// Indicate if the instruction has attached vouchers or not
		foreach($data as $id => &$row)
		{
//			// Append files ("Verifikat")
//			$row->files = [];
			if(!empty($row->external_id))
			{
				$dir = "/var/www/html/vouchers/{$row->external_id}";
				if(file_exists($dir))
				{
					$row->has_vouchers = true;
/*
					foreach(glob("{$dir}/*") as $file)
					{
						$row->files[] = basename($file);
					}
*/
					// Apply filter: Remove all instructions with a voucher
					if(!empty($filter_vouchers) && $filter_vouchers === false)
					{
						unset($data[$id]);
					}
				}
			}
			else
			{
				$row->has_vouchers = false;

				// Apply filter: Remove all instructions with a voucher
				if(!empty($filter_vouchers) && $filter_vouchers === true)
				{
					unset($data[$id]);
				}
			}
		}
		unset($row);

		// If we removed rows in the foreach above the indexing will be wrong, so we need to remove all keys.
		$data = array_values($data);

		$result = [
			"data" => $data
		];

		if($this->pagination != null)
		{
			$result["total"]    = $query->getCountForPagination();
			$result["per_page"] = $this->pagination;
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
					->leftJoin("accounting_period", "accounting_period.entity_id", "=", "accounting_instruction.accounting_period")
					->where("accounting_period.name", $op, $param);
				unset($filters[$id]);
			}
			else if("instruction_number" == $id)
			{
				// Filter on instruction_number
				$query = $query->where("accounting_instruction.instruction_number", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Join transactions table and calculate balance
		$query = $query
			->leftJoin("accounting_transaction", "accounting_transaction.accounting_instruction", "=", "entity.entity_id")
			->groupBy("entity.entity_id")
			->where("accounting_transaction.amount", ">", 0)
			->selectRaw("SUM(amount) AS balance");

		// Get result from database
		$data = (array)$query->first();

		// Generate an error if there is no such instruction
		if(empty($data))
		{
			return false;
		}

		// Create a new entity
		$entity = new AccountingInstruction;

		// Populate the entity with data
		foreach($data as $key => $value)
		{
			$entity->{$key} = $value;
		}

		// Load the transactions
		$entity->transactions = DB::table("entity")
			->join("accounting_transaction", "accounting_transaction.entity_id", "=", "entity.entity_id")
			->join("accounting_account", "accounting_transaction.accounting_account", "=", "accounting_account.entity_id")
			->join("entity AS e2", "accounting_account.entity_id", "=", "e2.entity_id")
			->where("accounting_instruction", "=", $entity->entity_id)
			->select(
				"entity.title",
				"entity.description",
				"accounting_transaction.amount AS balance",
				"accounting_account.account_number",
				"e2.title AS account_title"
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
				$entity = new AccountingTransaction;
				$entity->accounting_instruction = $this->entity_id;
				$entity->title                  = $transaction["title"];
				$entity->accounting_account     = $this->_getAccountEntityId($transaction["account_number"]);
				$entity->amount                 = $transaction["amount"];
				$entity->accounting_cost_center = $transaction["accounting_cost_center"] ?? null;
				$entity->external_id            = $transaction["external_id"] ?? null;

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

	protected function _getAccountEntityId($account_number)
	{
		return DB::table("accounting_account")->where("account_number", $account_number)->value("entity_id");
	}
}