<?php
namespace App\Models;

use App\Models\Entity;

//	protected $with = array("transactions");

// TODO: Ta hänsyn till accounting_period

class AccountingAccount extends Entity
{
	protected $type = "accounting_account";
	protected $join = "accounting_account";
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
		"account_number" => [
			"column" => "accounting_account.account_number",
			"select" => "accounting_account.account_number",
		],
		"accounting_period" => [
			"column" => "accounting_account.accounting_period",
			"select" => "accounting_account.accounting_period",
		],
	];
	protected $sort = ["account_number", "asc"];

	/**
	 *
	 */
	public function _list($filters = [])
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery();

		// Get account balance
		$query = $query->leftJoin("accounting_transaction", "accounting_account.entity_id", "=", "accounting_transaction.accounting_account")
			->groupBy("entity.entity_id")
			->selectRaw("COALESCE(SUM(amount), 0) AS balance");

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
					->leftJoin("accounting_period", "accounting_period.entity_id", "=", "accounting_account.accounting_period")
					->where("accounting_period.name", $op, $param);
				unset($filters[$id]);
			}
			// Filter on account balance
			else if("balance" == $id)
			{
				$query = $query->having("balance", $op, $param);
				unset($filters[$id]);
			}
			// Filter on number of transactions
			else if("transactions" == $id)
			{
				$query = $query->selectRaw("COUNT(accounting_transaction.entity_id) AS num_transactions");
				$query = $query->having("num_transactions", $op, $param);
				unset($filters[$id]);
			}
/*
			// Filter on account_number
			else if("account_number" == $id)
			{
				$query = $query->where("accounting_account.account_number", $filter[0], $filter[1]);
				unset($filters[$id]);
			}
*/
			// Pagination
			else if("per_page" == $id)
			{
				$this->pagination = $filter;
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Get result from database
		$data = $query->get();

		// Get ingoing balance
		foreach($data as &$row)
		{
			// Instruction with number 0 is always ingoing balance
			$ingoing = AccountingInstruction::load(
				[
					["instruction_number", "=", 0]
				]
			);
/*
			echo "<pre>a";
			print_r($ingoing);
			die();
			$row->balance_in = 0;
*/
			if(empty($ingoing))
			{
				continue;
			}

			// TODO: Vänt rätt på kredit/debet
			if($row->account_number >= 3000 && $row->account_number <= 8311)
			{
				$row->balance *= -1;
			}
			foreach($ingoing["transactions"] as $balance)
			{
				if($balance->account_number == $row->account_number)
				{
					$row->balance_in = $balance->balance;
				}
			}
		}
		unset($row);

		/*
		foreach($data as &$row)
		{
//			if(file_exists())
			{
				$row->files = "meep";
			}
		}
		*/

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

	/**
	 *
	 */
	public function _load($filters, $show_deleted = false)
	{
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
					->leftJoin("accounting_period", "accounting_period.entity_id", "=", "accounting_account.accounting_period")
					->where("accounting_period.name", $op, $param);
				unset($filters[$id]);
			}
			// Filter on account_number
			else if("account_number" == $id)
			{
				$query = $query->where("accounting_account.account_number", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Calculate sum of transactions
		$query = $query
			->leftJoin("accounting_transaction", "accounting_account.entity_id", "=", "accounting_transaction.accounting_account")
			->groupBy("entity.entity_id")
			->selectRaw("SUM(amount) AS balance");

		// Get result from database
		$data = (array)$query->first();

		// Create a new entity
		$entity = new AccountingAccount;

		// Populate the entity with data
		foreach($data as $key => $value)
		{
			$entity->{$key} = $value;
		}

		// Return account
		return $entity;
	}
}