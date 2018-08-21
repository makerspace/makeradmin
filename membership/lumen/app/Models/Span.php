<?php

namespace App\Models;

use Makeradmin\Models\Entity;
use DB;

/**
 *
 */
class Span extends Entity
{
	protected $type = "span";
	protected $table = "membership_spans";
	protected $id_column = "span_id";
	protected $deletable = false;
	protected $columns = [
		"span_id" => [
			"column" => "membership_spans.span_id",
			"select" => "membership_spans.span_id",
		],
		"member_id" => [
			"column" => "membership_spans.member_id",
			"select" => "membership_spans.member_id",
		],
		"startdate" => [
			"column" => "membership_spans.startdate",
			"select" => "DATE_FORMAT(membership_spans.startdate, '%Y-%m-%d')",
		],
		"enddate" => [
			"column" => "membership_spans.enddate",
			"select" => "DATE_FORMAT(membership_spans.enddate, '%Y-%m-%d')",
		],
		"span_type" => [
			"column" => "membership_spans.type",
			"select" => "membership_spans.type",
		],
		"creation_reason" => [
			"column" => "membership_spans.creation_reason",
			"select" => "membership_spans.creation_reason",
		],
		"created_at" => [
			"column" => "membership_spans.created_at",
			"select" => "DATE_FORMAT(membership_spans.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
	];

	protected $expandable_fields = [
		'member' => [
			'column' => 'member_id',
			'join_table' => 'membership_members',
			'join_column' => 'member_id',
			'join_type' => 'left',
			'selects' => [
				'member_number',
				'firstname',
				'lastname',
			],
		],
	];
	protected $sort = ["created_at", "desc"];
	protected $validation = [
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
					->where("membership_spans.member_id",       "like", "%".$word."%");
			});
		}

		return $query;
	}
}