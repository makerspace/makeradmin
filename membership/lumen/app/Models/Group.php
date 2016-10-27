<?php
namespace App\Models;

use App\Models\Entity;

/**
 *
 */
class Group extends Entity
{
	protected $type = "group";
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
	];
	protected $sort = ["title", "asc"];
	protected $validation = [
		"title" => ["required", "unique"],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
					->  where("entity.title",       "like", "%".$word."%")
					->orWhere("entity.description", "like", "%".$word."%");
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
		$query = $query
			->leftJoin("relation", "relation.entity2", "=", "entity.entity_id")
			->selectRaw("(SELECT COUNT(*) FROM relation LEFT JOIN entity e ON e.entity_id = relation.entity1 WHERE relation.entity2 = entity.entity_id AND e.type=\"member\") AS membercount");

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