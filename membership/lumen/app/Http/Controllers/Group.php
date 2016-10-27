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

class Group extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request, Authorizer $authorizer)
	{
		return $this->_applyStandardFilters("Group", $request);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$json = $request->json()->all();

		// Create new group
		$entity = new GroupModel;
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
	function read(Request $request, $entity_id)
	{
		// Load the group
		$entity = GroupModel::load($entity_id);

		// Generate an error if there is no such group
		if(false === $entity)
		{
			return Response()->json([
				"message" => "No group with specified group id",
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
	function update(Request $request, $entity_id)
	{
		// Load the group
		$entity = GroupModel::load($entity_id);
		// Generate an error if there is no such group
		if(false === $entity)
		{
			return Response()->json([
				"message" => "No group with specified entity id",
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
	function delete(Request $request, $entity_id)
	{
		$entity = GroupModel::load($entity_id);

		if($entity->delete())
		{
			return [
				"status" => "deleted"
			];
		}
		else
		{
			return [
				"status" => "error"
			];
		}
	}
}