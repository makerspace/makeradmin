<?php
namespace App\Models;

use App\Models\Entity;

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
		"title" => ["required"/*, "unique"*/],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
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
		$query = $this->_buildLoadQuery($filters);

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Calculate total number of peoples in the group
/*
		$query = $query
			->leftJoin("relation", "relation.entity2", "=", "entity.entity_id")
			->selectRaw("(SELECT COUNT(*) FROM relation LEFT JOIN entity e ON e.entity_id = relation.entity1 WHERE relation.entity2 = entity.entity_id AND e.type=\"member\") AS membercount");
*/
// TODO: Member count

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