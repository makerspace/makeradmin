<?php
namespace App\Models;

use App\Models\Entity;
use DB;

/**
 *
 */
class Mail extends Entity
{
	protected $type = "mail";
	protected $join = "mail";
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
		"type" => [
			"column" => "mail.type",
			"select" => "mail.type",
		],
		"recipient" => [
			"column" => "mail.recipient",
			"select" => "mail.recipient",
		],
		"status" => [
			"column" => "mail.status",
			"select" => "mail.status",
		],
		"date_sent" => [
			"column" => "mail.date_sent",
			// An ugly way to sort unsent messages first
			"select" => "IF(`date_sent` IS NULL, '2030-01-01 00:00:00', DATE_FORMAT(mail.date_sent, '%Y-%m-%dT%H:%i:%sZ'))",
		],
	];
	protected $sort = [
		["date_sent", "desc"],
		["created_at", "desc"]
	];

	/**
	 *
	 */
	public function _list($filters = [])
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery();

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
		$data = $query->get();

		foreach($data as $row)
		{
			// An ugly way to sort unsent messages first
			if($row->date_sent == "2030-01-01 00:00:00")
			{
				$row->date_sent = null;
			}
		}

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
}