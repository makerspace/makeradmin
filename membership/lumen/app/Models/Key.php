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
	protected $table = "membership_keys";
	protected $id_column = "key_id";
	protected $deletable = true;
	protected $columns = [
		"key_id" => [
			"column" => "membership_keys.rfid_id",
			"select" => "membership_keys.rfid_id",
		],
		"member_id" => [
			"column" => "membership_keys.member_id",
			"select" => "membership_keys.member_id",
		],
		"created_at" => [
			"column" => "membership_keys.created_at",
			"select" => "DATE_FORMAT(membership_keys.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_keys.updated_at",
			"select" => "DATE_FORMAT(membership_keys.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"description" => [
			"column" => "membership_keys.description",
			"select" => "membership_keys.description",
		],
		"tagid" => [
			"column" => "membership_keys.tagid",
			"select" => "membership_keys.tagid",
		],
	];
	protected $expands = [
		'member' => [
			'column' => 'member_id',
			'join_table' => 'membership_members',
			'join_column' => 'member_id',
			'selects' => [
				'member_number',
				'firstname',
				'lastname',
			],
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
					->orWhere("membership_keys.description", "like", "%".$word."%")
					->orWhere("membership_keys.tagid",       "like", "%".$word."%");
			});
		}

		return $query;
	}
}