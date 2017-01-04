<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Permission as PermissionModel;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

use DB;

class Permission extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request)
	{
		return $this->_applyStandardFilters("Permission", $request);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$json = $request->json()->all();

		// Create new permission
		$entity = new PermissionModel;
		$entity->role_id    = $json["role_id"]    ?? null;
		$entity->permission = $json["permission"] ?? null;
		$entity->group_id   = $json["group_id"]   ?? null;

		// Validate input
		$entity->validate();

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
	function read(Request $request, $permission_id)
	{
		// Load the entity
		$entity = PermissionModel::load([
			"permission_id" => $permission_id
		]);

		// Generate an error if there is no such permission
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "No permission with specified permission_id",
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
	function update(Request $request, $permission_id)
	{
		// Load the entity
		$entity = PermissionModel::load([
			"permission_id" => ["=", $permission_id]
		]);

		// Generate an error if there is no such permission
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "Could not find any permission with specified permission_id",
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
			"data" => $entity->toArray(),
		], 200);
	}

	/**
	 *
	 */
	function delete(Request $request, $permission_id)
	{
		// Load the entity
		$entity = PermissionModel::load([
			"permission_id" => ["=", $permission_id]
		]);

		return $this->_delete($entity);
	}
}