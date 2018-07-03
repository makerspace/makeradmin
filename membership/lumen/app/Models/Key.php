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
		"created_at" => [
			"column" => "membership_keys.created_at",
			"select" => "DATE_FORMAT(membership_keys.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_keys.updated_at",
			"select" => "DATE_FORMAT(membership_keys.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "membership_keys.title",
			"select" => "membership_keys.title",
		],
		"description" => [
			"column" => "membership_keys.description",
			"select" => "membership_keys.description",
		],
		"tagid" => [
			"column" => "membership_keys.tagid",
			"select" => "membership_keys.tagid",
		],
		"status" => [
			"column" => "membership_keys.status",
			"select" => "membership_keys.status",
		],
		"startdate" => [
			"column" => "membership_keys.startdate",
			"select" => "DATE_FORMAT(membership_keys.startdate, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"enddate" => [
			"column" => "membership_keys.enddate",
			"select" => "DATE_FORMAT(membership_keys.enddate, '%Y-%m-%dT%H:%i:%sZ')",
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
					->  where("membership_keys.title",       "like", "%".$word."%")
					->orWhere("membership_keys.description", "like", "%".$word."%")
					->orWhere("membership_keys.tagid",       "like", "%".$word."%");
			});
		}

		return $query;
	}
}