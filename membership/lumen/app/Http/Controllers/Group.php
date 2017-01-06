<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Group as GroupModel;
use App\Models\Member as MemberModel;

use App\Traits\EntityStandardFiltering;

use DB;

class Group extends Controller
{
	use EntityStandardFiltering;

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
http://mikehillyer.com/articles/managing-hierarchical-data-in-mysql/
https://rogerkeays.com/how-to-move-a-node-in-nested-sets-with-sql
https://www.percona.com/blog/2011/02/14/moving-subtrees-in-closure-table/
http://stackoverflow.com/questions/2801285/move-node-in-nested-sets-tree
https://github.com/werc/TreeTraversal
http://we-rc.com/blog/2015/07/19/nested-set-model-practical-examples-part-i

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
		return Response()->json($result, 200);
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
		$entity->name        = $json["name"]        ?? null;
		$entity->title       = $json["title"]       ?? null;
		$entity->description = $json["description"] ?? null;

		// Validate input
//		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "created",
			"data" => $entity->toArray(),
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
			// Send response to client
			return Response()->json([
				"data" => $entity->toArray(),
			], 200);
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
		$entity->name        = $json["name"]        ?? null;
		$entity->title       = $json["title"]       ?? null;
		$entity->description = $json["description"] ?? null;

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return [
			"status" => "updated",
			"data" => $entity->toArray(),
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

		return $this->_delete($entity);
	}

	/**
	 * Get all members in a group
	 */
	function getMembers(Request $request, $group_id)
	{
		// Paging filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
			"group_id" => $group_id,
		];

		// Filter on relations
/*
		if(!empty($request->get("relations")))
		{
			$filters["relations"] = $request->get("relations");
		}
*/

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
		$result = MemberModel::list($filters);

		// Return json array
		return Response()->json($result, 200);
	}
}