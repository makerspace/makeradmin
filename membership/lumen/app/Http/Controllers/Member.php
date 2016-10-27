<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Member as MemberModel;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

use DB;

class Member extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request)
	{
		return $this->_applyStandardFilters("Member", $request);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$json = $request->json()->all();

		// TODO: This should be removed
		// Create a unique member number if not specified
		if(!empty($json["member_number"]))
		{
			$member_number = $json["member_number"];
		}
		else
		{
			$newest_member = MemberModel::load([
				["sort", ["member_number", "desc"]]
			]);

			if(empty($newest_member))
			{
				$member_number = 1;
			}
			else
			{
				$member_number = ($newest_member->member_number + 1);
			}
		}

		// Create new member
		$entity = new MemberModel;
		$entity->member_number   = $member_number;
		$entity->email           = $json["email"];
		$entity->password        = $json["password"]        ?? null;
		$entity->firstname       = $json["firstname"]       ?? null;
		$entity->lastname        = $json["lastname"]        ?? null;
		$entity->civicregno      = $json["civicregno"]      ?? null;
		$entity->company         = $json["company"]         ?? null;
		$entity->orgno           = $json["orgno"]           ?? null;
		$entity->address_street  = $json["address_street"]  ?? null;
		$entity->address_extra   = $json["address_extra"]   ?? null;
		$entity->address_zipcode = $json["address_zipcode"] ?? null;
		$entity->address_city    = $json["address_city"]    ?? null;
		$entity->address_country = $json["address_country"] ?? "SE";
		$entity->phone           = $json["phone"]           ?? null;

		// Add relations
		if(!empty($json["relations"]))
		{
			$entity->addRelations($json["relations"]);
		}

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
	function read(Request $request, $member_number)
	{
		// Load the entity
		$entity = MemberModel::load([
			"member_number" => $member_number
		]);

		// Generate an error if there is no such member
		if(false === $entity)
		{
			return Response()->json([
				"message" => "No member with specified member number",
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
	function update(Request $request, $member_number)
	{
		// Load the entity
		$entity = MemberModel::load([
			["member_number", "=", $member_number]
		]);

		// Generate an error if there is no such product
		if(false === $entity)
		{
			return Response()->json([
				"message" => "Could not find any member with specified member_number",
			], 404);
		}

		$json = $request->json()->all();

		// Populate the entity with new values
		foreach($json as $key => $value)
		{
			$entity->{$key} = $value ?? null;
		}
/*
		// TODO: Validate input
		// TODO: Validation of tagid will fail because it is already in the database en therefore not unique
		$errors = $entity->validate();
		if(!empty($errors))
		{
			return Response()->json([
				"errors" => $errors,
			], 400);
		}
*/
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
	function delete(Request $request, $member_number)
	{
		// Load the entity
		$entity = MemberModel::load([
			["member_number", "=", $member_number]
		]);

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