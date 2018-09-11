<?php
namespace App\Models;

use Makeradmin\Models\Entity;

/**
 *
 */
class Group extends Entity
{
	protected $type = "group";
	protected $table = "membership_groups";
	protected $id_column = "group_id";
	protected $columns = [
		"group_id" => [
			"column" => "membership_groups.group_id",
			"select" => "membership_groups.group_id",
		],
		"parent" => [
			"column" => "membership_groups.parent",
			"select" => "membership_groups.parent",
		],
		"created_at" => [
			"column" => "membership_groups.created_at",
			"select" => "DATE_FORMAT(membership_groups.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_groups.updated_at",
			"select" => "DATE_FORMAT(membership_groups.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"name" => [
			"column" => "membership_groups.name",
			"select" => "membership_groups.name",
		],
		"title" => [
			"column" => "membership_groups.title",
			"select" => "membership_groups.title",
		],
		"description" => [
			"column" => "membership_groups.description",
			"select" => "membership_groups.description",
		],
	];
	protected $sort = ["title", "asc"];
	protected $validation = [
		"name"  => ["required"/*, "unique"*/],
		"title" => ["required"],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
					->  where("membership_groups.name",        "like", "%".$word."%")
					->  where("membership_groups.title",       "like", "%".$word."%")
					->orWhere("membership_groups.description", "like", "%".$word."%");
			});
		}

		return $query;
	}

	protected function _list($filters = [])
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

			// Filter on member_id
			if("member_id" == $id)
			{
				$query = $query
					->leftJoin("membership_members_groups", "membership_members_groups.group_id", "=", "membership_groups.group_id")
					->where("membership_members_groups.member_id", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Calculate total number of peoples in the group
		$query = $query
			->leftJoin("membership_members_groups AS gm", "gm.group_id", "=", "membership_groups.group_id")
			->selectRaw("COUNT(gm.member_id) AS num_members")
			->groupBy("membership_groups.group_id");

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$data = $query->get();

		// Prepare array to be returned
		$result = [
			"data" => $data
		];

		// Pagination
		if($this->pagination != null)
		{
			$result["total"]     = $query->getCountForPagination();
			$result["per_page"]  = $this->pagination;
			$result["last_page"] = ceil($result["total"] / $result["per_page"]);
		}

		return $result;
	}
}