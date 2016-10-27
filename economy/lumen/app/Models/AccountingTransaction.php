<?php
namespace App\Models;
use DB;

class AccountingTransaction extends Entity
{
	protected $type = "accounting_transaction";
	protected $join = "accounting_transaction";
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
			"column" => "DATE_FORMAT(entity.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
			"select" => "DATE_FORMAT(entity.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"transaction_title" => [
			"column" => "entity.title",
			"select" => "entity.title",
		],
		"transaction_description" => [
			"column" => "entity.description",
			"select" => "entity.description",
		],
		"accounting_instruction" => [
			"column" => "accounting_transaction.accounting_instruction",
			"select" => "accounting_transaction.accounting_instruction",
		],
		"accounting_account" => [
			"column" => "accounting_transaction.accounting_account",
			"select" => "accounting_transaction.accounting_account",
		],
		"accounting_cost_center" => [
			"column" => "accounting_transaction.accounting_cost_center",
			"select" => "accounting_transaction.accounting_cost_center",
		],
		"amount" => [
			"column" => "accounting_transaction.amount",
			"select" => "accounting_transaction.amount",
		],
		"external_id" => [
			"column" => "accounting_transaction.external_id",
			"select" => "accounting_transaction.external_id",
		],
		"instruction_title" => [
			"column" => "ie.title",
			"select" => "ie.title",
		],
		"instruction_number" => [
			"column" => "accounting_instruction.instruction_number",
			"select" => "accounting_instruction.instruction_number",
		],
		"accounting_date" => [
			"column" => "accounting_instruction.accounting_date",
			"select" => "accounting_instruction.accounting_date",
		],
		"extid" => [
			"column" => "accounting_instruction.external_id",
			"select" => "accounting_instruction.external_id",
		],
	];
	protected $sort = ["accounting_date", "desc"];

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
			// Filter on accounting period
			else if("account_number" == $id)
			{
				$query = $query
					->leftJoin("accounting_account", "accounting_account.entity_id", "=", "accounting_transaction.accounting_account")
					->where("accounting_account.account_number", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Load the instruction
		$query = $query
			->leftJoin("accounting_instruction", "accounting_instruction.entity_id", "=", "accounting_transaction.accounting_instruction")
			->leftJoin("entity AS ie", "ie.entity_id", "=", "accounting_instruction.entity_id");

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$result = $query->get();
		$data = [];
		$balance = 0;
		foreach($result as $row)
		{
			if(!empty($row->extid))
			{
				$dir = "/var/www/html/vouchers/{$row->extid}";
				if(file_exists($dir))
				{
					$row->files = "x";
				}
			}

			$balance += $row->amount;
			$row->balance = $balance;
			$data[] = $row;
		}

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
}