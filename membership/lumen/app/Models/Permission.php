<?php
namespace App\Models;

use Makeradmin\Models\Entity;

/**
 *
 */
class Permission extends Entity
{
	protected $type = "permission";
	protected $table = "membership_permissions";
	protected $id_column = "permission_id";
	protected $columns = [
		"permission_id" => [
			"column" => "membership_permissions.permission_id",
			"select" => "membership_permissions.permission_id",
		],
		"role_id" => [
			"column" => "membership_permissions.role_id",
			"select" => "membership_permissions.role_id",
		],
		"created_at" => [
			"column" => "membership_permissions.created_at",
			"select" => "DATE_FORMAT(membership_permissions.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_permissions.updated_at",
			"select" => "DATE_FORMAT(membership_permissions.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"permission" => [
			"column" => "membership_permissions.permission",
			"select" => "membership_permissions.permission",
		],
		"group_id" => [
			"column" => "membership_permissions.group_id",
			"select" => "membership_permissions.group_id",
		],
	];
	protected $sort = ["permission_id", "desc"];
	protected $validation = [
		"permission" => ["required", "unique"],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// Build the search query
				$query
				->  where("membership_permissions.permission",    "like", "%".$word."%")
				->orWhere("membership_permissions.permission_id", "like", "%".$word."%");
			});
		}
		return $query;
	}
}