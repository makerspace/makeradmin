<?php
namespace App\Traits;

trait EntityStandardFiltering
{
	/**
	 *
	 */
	protected function _list($model, $params)
	{
		// Paging filter
		$filters = [];

		// Number of entities per page
		if(array_key_exists("per_page", $params))
		{
			// Use the specified per_page setting, if provided
			$per_page = $params["per_page"];

			if(is_numeric($per_page) && $per_page > 0)
			{
				$per_page = (int)$per_page;
			}

			unset($params["per_page"]);
		}
		$params["per_page"] = $per_page ?? 25;

		// Pagination
		if(array_key_exists("page", $params))
		{
			unset($params["page"]);
		}

		// Sorting
		if(array_key_exists("sort_by", $params))
		{
			if(!empty($params["sort_by"]))
			{
				// Apply sorting filter
				$order = ($params["sort_order"] == "desc" ? "desc" : "asc");
				$filters["sort"] = [$params["sort_by"], $order];
			}

			// Remove from params
			unset($params["sort_by"]);
			unset($params["sort_order"]);
		}

		// Filter on one or more entity_id
		if(array_key_exists("entity_id", $params))
		{
			if(!empty($params["entity_id"]))
			{
				// Apply entity_id filter
				$filters["entity_id"] = explode(",", $params["entity_id"]);
			}

			// Remove from params
			unset($params["entity_id"]);
		}

		// All other params as arbritrary parameters
		foreach($params as $key => $value)
		{
			$filters[$key] = $value;
		}

		// Load data from database
		$result = call_user_func("\App\Models\\{$model}::list", $filters);

		// Return json array
		return Response()->json($result, 200);
	}

	/**
	 * Generic read function for entities
	 */
	protected function _create($model, $attributes)
	{
		$m = "\App\Models\\{$model}";
		$entity = new $m;

		// Populate the entity with new values
		$this->_setAttributes($entity, $attributes);

		// Validate input
		$entity->validate();

		// Save entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "created",
			"data" => $entity->toArray(),
		], 201);
	}

	/**
	 * Generic read function for entities
	 */
	protected function _read($model, $data)
	{
		// Load the entity
		$entity = call_user_func("\App\Models\\{$model}::load", $data);

		// Generate an error if there is no such rfid entity
		if(false === $entity)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Could not find any entity with specified parameters",
			], 404);
		}
		else
		{
			return Response()->json([
				"data" => $entity->toArray(),
			], 200);
		}
	}

	/**
	 * Generic update function for entities
	 */
	protected function _update($model, $data, $attributes)
	{
		// Load the entity
		$entity = call_user_func("\App\Models\\{$model}::load", $data);

		// Generate an error if there is no such rfid entity
		if(false === $entity)
		{
			return Response()->json([
				"message" => "Could not find any entity with specified parameters",
			], 404);
		}

		// Populate the entity with new values
		$this->_setAttributes($entity, $attributes);

		// Change the update_at value, if not provided in the input
		if($entity->updated_at === null)
		{
			$entity->updated_at = date("c");
		}

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Send response to client
		return Response()->json([
			"status" => "updated",
			"data" => $entity->toArray(),
		], 200);
	}

	/**
	 * Generic delete function for entities
	 */
	protected function _delete($model, $data)
	{
		// Load the entity
		$entity = call_user_func("\App\Models\\{$model}::load", $data);

		// Generate an error if there is no such entity
		if(false === $entity)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Could not find any entity with specified parameters",
			], 404);
		}

		if($entity->delete())
		{
			return Response()->json([
				"status"  => "deleted",
				"message" => "The entity was successfully deleted",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "error",
				"message" => "An error occured when trying to delete the entity",
			], 500);
		}
	}

	/**
	 * Generic function for setting/updating the attributes on a model
	 */
	protected function _setAttributes(&$entity, $attributes)
	{
		foreach($attributes as $key => $value)
		{
			// Prevent columns that could not be updated
			if(
				("entity_id"  === $key) ||
				("created_at" === $key && $value === null)
			)
			{
				continue;
			}

			// Update the value
			$entity->{$key} = $value ?? null;
		}
	}
}