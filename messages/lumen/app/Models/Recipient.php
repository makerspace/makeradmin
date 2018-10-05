<?php
namespace App\Models;

use Makeradmin\Models\Entity;
use DB;

/**
 *
 */
class Recipient extends Entity
{
	protected $type = "recipient";
	protected $table = "messages_recipient";
	protected $id_column = "recipient_id";
	protected $soft_deletable = false;
	protected $columns = [
		"recipient_id" => [
			"column" => "messages_recipient.messages_recipient_id",
			"select" => "messages_recipient.messages_recipient_id",
		],
		"created_at" => [
			"column" => "messages_recipient.created_at",
			"select" => "DATE_FORMAT(messages_recipient.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "messages_recipient.updated_at",
			"select" => "DATE_FORMAT(messages_recipient.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"message_id" => [
			"column" => "messages_recipient.messages_message_id",
			"select" => "messages_recipient.messages_message_id",
		],
		"subject" => [
			"column" => "messages_recipient.title",
			"select" => "messages_recipient.title",
		],
		"body" => [
			"column" => "messages_recipient.description",
			"select" => "messages_recipient.description",
		],
		"member_id" => [
			"column" => "messages_recipient.member_id",
			"select" => "messages_recipient.member_id",
		],
		"recipient" => [
			"column" => "messages_recipient.recipient",
			"select" => "messages_recipient.recipient",
		],
		"date_sent" => [
			"column" => "messages_recipient.date_sent",
			// An ugly way to sort unsent messages first
			"select" => "IF(`date_sent` IS NULL, '2030-01-01 00:00:00', DATE_FORMAT(messages_recipient.date_sent, '%Y-%m-%dT%H:%i:%sZ'))",
		],
		"status" => [
			"column" => "messages_recipient.status",
			"select" => "messages_recipient.status",
		],
	];
	protected $sort = [
		["recipient_id", "desc"]
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

		// Include message type
		$query = $query
			->leftJoin("messages_message", "messages_message.messages_message_id", "=", "messages_recipient.messages_message_id")
//			->groupBy("messages_message.messages_message_id")
			->selectRaw("messages_message.message_type AS message_type");

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