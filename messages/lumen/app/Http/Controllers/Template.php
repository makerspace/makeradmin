<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Template as TemplateModel;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

class Template extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 * Return a list of all queued/sent messages
	 */
	function list(Request $request)
	{
		return $this->_applyStandardFilters("Template", $request);
	}

	/**
	 * Load a queued/sent messages
	 */
	function read(Request $request, $template_id)
	{
		// Load the product
		$template = TemplateModel::load([
			"template_id" => ["=", $template_id]
		]);

		// Generate an error if there is no such product
		if(false === $template)
		{
			return Response()->json([
				"message" => "No product with specified product id",
			], 404);
		}
		else
		{
			return Response()->json([
				"data" => $template->toArray(),
			], 200);
		}
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$json = $request->json()->all();

		// Create new template
		$entity = new TemplateModel;
		$entity->name        = $json["name"]        ?? null;
		$entity->title       = $json["title"]       ?? null;
		$entity->description = $json["description"] ?? null;

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
	function update(Request $request, $template_id)
	{
		// Load the entity
		$entity = TemplateModel::load([
			"template_id" => ["=", $template_id]
		]);

		// Generate an error if there is no such member
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "Could not find any template with specified template_id",
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

		return Response()->json([
			"status" => "updated",
			"data" => $entity->toArray(),
		], 200);
	}

	/**
	 *
	 */
	function delete(Request $request, $template_id)
	{
		// Load the entity
		$entity = TemplateModel::load([
			"template_id" => ["=", $template_id]
		]);

		return $this->_delete($entity);
	}
}