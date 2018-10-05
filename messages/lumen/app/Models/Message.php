<?php
namespace App\Models;

use Makeradmin\Models\Entity;
use DB;

/**
 *
 */
class Message extends Entity
{
	protected $type = "message";
	protected $table = "messages_message";
	protected $id_column = "message_id";
	protected $soft_deletable = false;
	protected $columns = [
		"message_id" => [
			"column" => "messages_message.messages_message_id",
			"select" => "messages_message.messages_message_id",
		],
		"created_at" => [
			"column" => "messages_message.created_at",
			"select" => "DATE_FORMAT(messages_message.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "messages_message.updated_at",
			"select" => "DATE_FORMAT(messages_message.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"subject" => [
			"column" => "messages_message.title",
			"select" => "messages_message.title",
		],
		"body" => [
			"column" => "messages_message.description",
			"select" => "messages_message.description",
		],
		"message_type" => [
			"column" => "messages_message.message_type",
			"select" => "messages_message.message_type",
		],
		"status" => [
			"column" => "messages_message.status",
			"select" => "messages_message.status",
		],
	];
	protected $sort = [
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

		// Include the number of recipients
		$query = $query
			->leftJoin("messages_recipient", "messages_recipient.messages_message_id", "=", "messages_message.messages_message_id")
			->groupBy("messages_message.messages_message_id")
			->selectRaw("COUNT(messages_recipient.messages_recipient_id) AS num_recipients");

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

	/**
	 *
	 */
	public function _load($filters, $show_deleted = false)
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery();

		// Include the number of recipients
		$query = $query
			->leftJoin("messages_recipient", "messages_recipient.messages_message_id", "=", "messages_message.messages_message_id")
			->groupBy("messages_message.messages_message_id")
			->selectRaw("COUNT(messages_recipient.messages_recipient_id) AS num_recipients");

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Get data from database
		$data = (array)$query->first();

		// Return false if no entity was found in database
		if(empty($data))
		{
			return false;
		}

		// Create a new entity based on type
		$entity = new Message;

		// Populate the entity with data
		foreach($data as $key => $value)
		{
			$entity->{$key} = $value;
		}

		return $entity;
	}
}