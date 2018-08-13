<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Group as GroupModel;
use App\Models\Member as MemberModel;

use Makeradmin\Traits\EntityStandardFiltering;

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

	function _get_user_roles($user_id)
	{
		return DB::table("membership_members_roles")->select("role_id")->where("member_id", "=", $user_id);
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
		// Get all query string parameters
		$params = $request->query->all();
		return $this->_list("Group", $params);
	}

	/**
	 *
	 */
	function create(Request $request)
	{

		$json = $request->json()->all();

		// Create new group
		$entity = new GroupModel;
		$entity->parent      = $json["parent"]      ?? 0;
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
		return $this->_read("Group", [
			"group_id" => $group_id
		]);
	}

	/**
	 *
	 */
	function update(Request $request, $group_id)
	{
		$data = $request->json()->all();
		return $this->_update("Group", [
			"group_id" => $group_id
		], $data);
	}

	/**
	 * Delete group
	 */
	function delete(Request $request, $group_id)
	{
		return $this->_delete("Group", [
			"group_id" => $group_id,
		]);
	}

	/**
	 * Get all members in a group
	 */
	function getMembers(Request $request, $group_id)
	{
		// Get all query string parameters
		$params = $request->query->all();

		// Filter on group
		$params["group_id"] = $group_id;

		return $this->_list("Member", $params);
	}

	/**
	 * Get all permissions for a group
	 */
	function listPermissions(Request $request, $group_id) {
		// Get permissions for group
		// TODO: Groups are arranged into a hierarchy which should be expanded
		$permissions = DB::table("membership_group_permissions")
			->join("membership_permissions", "membership_permissions.permission_id",
			"membership_group_permissions.permission_id")
			->where('membership_group_permissions.group_id', $group_id)
			->select('membership_permissions.permission_id','permission')
			->get();

		// Send response to client
		return Response()->json([
			"data" => $permissions
		], 200);
	}

	/**
	 * Add a permission to a group
	 */
	public function addPermissions(Request $request, $group_id)
	{
		$json = $request->json()->all();

		// Add the group to the user
		$data = [];
		foreach($json["permissions"] as $permission_id)
		{
			DB::insert("REPLACE INTO membership_group_permissions(group_id, permission_id) VALUES(?, ?)", [$group_id, $permission_id]);
		}

		return Response()->json([
			"status"  => "ok",
		], 200);
	}

	/**
	 * Remove a permission from a group
	 */
	public function removePermissions(Request $request, $group_id)
	{
		$json = $request->json()->all();

		// Add the group to the user
		$data = [];
		foreach($json["permissions"] as $permission_id)
		{
			DB::insert("DELETE FROM membership_group_permissions WHERE group_id = ? AND permission_id = ?", [$group_id, $permission_id]);
		}

		return Response()->json([
			"status"  => "ok",
		], 200);
	}
}
