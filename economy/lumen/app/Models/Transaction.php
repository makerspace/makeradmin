<?php
namespace App\Models;
use DB;

class Transaction extends Entity
{
	protected $type = "transaction";
	protected $table = "economy_transaction";
	protected $id_column = "transaction_id";
	protected $columns = [
		"transaction_id" => [
			"column" => "economy_transaction.economy_transaction_id",
			"select" => "economy_transaction.economy_transaction_id",
		],
		"created_at" => [
			"column" => "economy_transaction.created_at",
			"select" => "DATE_FORMAT(economy_transaction.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "DATE_FORMAT(economy_transaction.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
			"select" => "DATE_FORMAT(economy_transaction.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"transaction_title" => [
			"column" => "economy_transaction.title",
			"select" => "economy_transaction.title",
		],
		"transaction_description" => [
			"column" => "economy_transaction.description",
			"select" => "economy_transaction.description",
		],
		"instruction_id" => [
			"column" => "economy_transaction.economy_instruction_id",
			"select" => "economy_transaction.economy_instruction_id",
		],
		"account_id" => [
			"column" => "economy_transaction.economy_account_id",
			"select" => "economy_transaction.economy_account_id",
		],
		"costcenter_id" => [
			"column" => "economy_transaction.economy_costcenter_id",
			"select" => "economy_transaction.economy_costcenter_id",
		],
		"amount" => [
			"column" => "economy_transaction.amount",
			"select" => "economy_transaction.amount",
		],
		"external_id" => [
			"column" => "economy_transaction.external_id",
			"select" => "economy_transaction.external_id",
		],
		"instruction_title" => [
			"column" => "economy_instruction.title",
			"select" => "economy_instruction.title",
		],
		"instruction_number" => [
			"column" => "economy_instruction.instruction_number",
			"select" => "economy_instruction.instruction_number",
		],
		"accounting_date" => [
			"column" => "economy_instruction.accounting_date",
			"select" => "DATE_FORMAT(economy_instruction.accounting_date, '%Y-%m-%d')",
		],
		"extid" => [
			"column" => "economy_instruction.external_id",
			"select" => "economy_instruction.external_id",
		],
		"period" => [
			"column" => "economy_accountingperiod.name",
			"select" => "economy_accountingperiod.name",
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

		// Load the instruction
		$query = $query
			->leftJoin("economy_instruction", "economy_instruction.economy_instruction_id", "=", "economy_transaction.economy_instruction_id");

		// Load the accounting period
		$query = $query
			->leftJoin("economy_accountingperiod", "economy_accountingperiod.economy_accountingperiod_id", "=", "economy_instruction.economy_accountingperiod_id");

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
					->where("economy_accountingperiod.name", $op, $param);
				unset($filters[$id]);
			}
			// Filter on accounting period
			else if("account_number" == $id)
			{
				$query = $query
					->leftJoin("economy_account", "economy_account.economy_account_id", "=", "economy_transaction.economy_account_id")
					->where("economy_account.account_number", $op, $param);
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