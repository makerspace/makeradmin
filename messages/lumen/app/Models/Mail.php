<?php
namespace App\Models;

use App\Models\Entity;
use DB;

/**
 *
 */
class Mail extends Entity
{
	protected $type = "queue";
	protected $table = "messages_queue";
	protected $id_column = "queue_id";
	protected $columns = [
		"queue_id" => [
			"column" => "messages_queue.messages_queue_id",
			"select" => "messages_queue.messages_queue_id",
		],
		"created_at" => [
			"column" => "messages_queue.created_at",
			"select" => "DATE_FORMAT(messages_queue.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "messages_queue.updated_at",
			"select" => "DATE_FORMAT(messages_queue.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "messages_queue.title",
			"select" => "messages_queue.title",
		],
		"description" => [
			"column" => "messages_queue.description",
			"select" => "messages_queue.description",
		],
		"type" => [
			"column" => "messages_queue.type",
			"select" => "messages_queue.type",
		],
		"recipient" => [
			"column" => "messages_queue.recipient",
			"select" => "messages_queue.recipient",
		],
		"status" => [
			"column" => "messages_queue.status",
			"select" => "messages_queue.status",
		],
		"date_sent" => [
			"column" => "messages_queue.date_sent",
			// An ugly way to sort unsent messages first
			"select" => "IF(`date_sent` IS NULL, '2030-01-01 00:00:00', DATE_FORMAT(messages_queue.date_sent, '%Y-%m-%dT%H:%i:%sZ'))",
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
//			$query->paginate($this->pagination);
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