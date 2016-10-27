<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Role as RoleModel;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

use DB;

class Role extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request)
	{
		return $this->_applyStandardFilters("Role", $request);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$json = $request->json()->all();

		// Create new role
		$entity = new RoleModel;
		$entity->group_id    = $json["group_id"]    ?? null;
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
	function read(Request $request, $role_id)
	{
		// Load the entity
		$entity = RoleModel::load([
			"role_id" => $role_id
		]);

		// Generate an error if there is no such role
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "No role with specified role_id",
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
	function update(Request $request, $role_id)
	{
		// Load the entity
		$entity = RoleModel::load([
			"role_id" => ["=", $role_id]
		]);

		// Generate an error if there is no such role
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "Could not find any role with specified role_id",
			], 404);
		}

		$json = $request->json()->all();

		// Populate the entity with new values
		foreach($json as $key => $value)
		{
			$entity->{$key} = $value ?? null;
		}

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// TODO: Standarized output
		return Response()->json([
			"status" => "updated",
			"entity" => $entity->toArray(),
		], 200);
	}

	/**
	 *
	 */
	function delete(Request $request, $role_id)
	{
		// Load the entity
		$entity = PermissionModel::load([
			"role_id" => ["=", $role_id]
		]);

		// Generate an error if there is no such role
		if(false === $entity)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Could not find any role with specified role_id",
			], 404);
		}

		if($entity->delete())
		{
			return Response()->json([
				"status"  => "deleted",
				"message" => "The role was successfully deleted",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "error",
				"message" => "An error occured when trying to delete role",
			], 500);
		}
	}
}