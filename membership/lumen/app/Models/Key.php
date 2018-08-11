<?php

namespace App\Models;

use Makeradmin\Models\Entity;
use DB;

/**
 *
 */
class Key extends Entity
{
	protected $type = "key";
	protected $table = "membership_rfid";
	protected $id_column = "key_id";
	protected $deletable = true;
	protected $columns = [
		"key_id" => [
			"column" => "membership_rfid.rfid_id",
			"select" => "membership_rfid.rfid_id",
		],
		"member_id" => [
			"column" => "membership_rfid.member_id",
			"select" => "membership_rfid.member_id",
		],
		"created_at" => [
			"column" => "membership_rfid.created_at",
			"select" => "DATE_FORMAT(membership_rfid.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_rfid.updated_at",
			"select" => "DATE_FORMAT(membership_rfid.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"description" => [
			"column" => "membership_rfid.description",
			"select" => "membership_rfid.description",
		],
		"tagid" => [
			"column" => "membership_rfid.tagid",
			"select" => "membership_rfid.tagid",
		],
	];
	protected $sort = ["created_at", "desc"];
	protected $validation = [
//		"tagid" => ["unique", "required"],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
					->  where("membership_rfid.title",       "like", "%".$word."%")
					->orWhere("membership_rfid.description", "like", "%".$word."%")
					->orWhere("membership_rfid.tagid",       "like", "%".$word."%");
			});
		}

		return $query;
	}
}