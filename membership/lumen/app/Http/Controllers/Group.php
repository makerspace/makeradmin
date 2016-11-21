<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Group as GroupModel;
use App\Models\Entity;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

use LucaDegasperi\OAuth2Server\Authorizer;

use DB;

class Group extends Controller
{
	use Pagination, EntityStandardFiltering;

	function _loadPermissions($roles)
	{
		$this->permissions = DB::table("membership_permissions")
			->whereIn("role_id", $roles)
			->get();
	}

	function _checkPermission($permission)
	{
		$groups = [];
		foreach($this->permissions as $p)
		{
			if($p->permission == $permission)
			{
				$groups[] = $p->group_id;
			}
		}

		// Get a list of all groups including children
		$all_groups = DB::table("membership_groups AS node")
			->join("membership_groups AS parent", function($join) {
				$join->whereRaw("`node`.`left` BETWEEN `parent`.`left` AND `parent`.`right`");
			})
			->select("node.group_id")
			->distinct()
			->whereIn("parent.group_id", $groups)
			->pluck("group_id");

		return $all_groups;
	}

/*
Full tree:
	SELECT node.title
	FROM membership_groups AS node,
		membership_groups AS parent
	WHERE node.`left` BETWEEN parent.`left` AND parent.`right`
		AND parent.group_id IN (16, 18)
	ORDER BY node.`left`;

Leaf nodes:
	SELECT title
	FROM membership_groups
	WHERE `right` = `left` + 1;

Single path:
	SELECT parent.title
	FROM membership_groups AS node,
		membership_groups AS parent
	WHERE node.`left` BETWEEN parent.`left` AND parent.`right`
		AND node.title = 'FLASH'
	ORDER BY parent.`left`;

Depth:
	SELECT node.title, (COUNT(parent.title) - 1) AS depth
	FROM membership_groups AS node,
		membership_groups AS parent
	WHERE node.`left` BETWEEN parent.`left` AND parent.`right`
	GROUP BY node.title
	ORDER BY node.`left`;

Indented:
	SELECT
		CONCAT(REPEAT('-', (COUNT(parent.title) - 1)), node.title) AS title,
		count(parent.title) AS depth
	FROM membership_groups AS node,
		membership_groups AS parent
	WHERE `node`.`left` BETWEEN `parent`.`left` AND `parent`.`right`
	GROUP BY `node`.`title`, `node`.`left`
	ORDER BY `node`.`left`;
*/

	/**
	 *
	 */
	function list(Request $request)
	{
		// TODO: Get roles from user
		$roles = [2, 5];

		// Get groups the where the user have a "view group" permission
		$this->_loadPermissions($roles);
		$groups = $this->_checkPermission("view group");

		// Paging and permission filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
			"group_id" => ["in", $groups],
		];

		// Filter on search
		if(!empty($request->get("search")))
		{
			$filters["search"] = $request->get("search");
		}

		// Sorting
		if(!empty($request->get("sort_by")))
		{
			$order = ($request->get("sort_order") == "desc" ? "desc" : "asc");
			$filters["sort"] = [$request->get("sort_by"), $order];
		}

		// Load data from database
		$result = call_user_func("\App\Models\\Group::list", $filters);

		// Return json array
		return $result;
	}

	/**
	 *
	 */
	function create(Request $request)
	{

		$json = $request->json()->all();

		// Create new group
		$entity = new GroupModel;
		$entity->parent      = $json["parent"]      ?? "null";
		$entity->title       = $json["title"]       ?? null;
		$entity->description = $json["description"] ?? null;

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "created",
			"entity" => $entity->toArray(),
		], 201);
	}

	/**
	 *
	 */
	function read(Request $request, $group_id)
	{
		// Load the group
		$entity = GroupModel::load([
			"group_id" => $group_id,
		]);

		// Generate an error if there is no such group
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "No group with specified group_id",
			], 404);
		}
		else
		{
			return $entity->toArray();
		}
	}

	/**
	 *
	 */
	function update(Request $request, $group_id)
	{
		// Load the group
		$entity = GroupModel::load([
			"group_id" => $group_id,
		]);

		// Generate an error if there is no such group
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "No group with specified group_id",
			], 404);
		}

		$json = $request->json()->all();

		// Create new group
		// TODO: Put in generic function
		$entity->title       = $json["title"]       ?? null;
		$entity->description = $json["description"] ?? null;

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// TODO: Standarized output
		return [
			"status" => "updated",
			"entity" => $entity->toArray(),
		];
	}

	/**
	 * Delete group
	 */
	function delete(Request $request, $group_id)
	{
		// Load the group
		$entity = GroupModel::load([
			"group_id" => $group_id,
		]);

		// Generate an error if there is no such group
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "No group with specified group_id",
			], 404);
		}

		if($entity->delete())
		{
			return [
				"status" => "deleted",
			];
		}
		else
		{
			return [
				"status" => "error",
			];
		}
	}
}