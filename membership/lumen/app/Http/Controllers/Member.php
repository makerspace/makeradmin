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
/*
		$user = $request->header("X-Username");
		$org  = $request->header("X-Organisation");

		if($user != "chille")
		{
			// Send response to client
			return Response()->json([
				"status"  => "error",
				"message" => "Access denied",
			], 403);
		}
*/
		/*
			En header specificerar vilken orgainsation/grupp man arbetar mot
				Riksorg = allt
				Förening / arbetsgrupp = begränsa till dess användare + kolla behörigheter
				Användare = access denied

			if($user == admin)
			{
				// Access to everything
			}
			else if($user == invidual member)
			{
				// Access only to self
			}
			else
			{
				//
			}

			Permissions:
				Admin    = Hämta samtliga users
				User     = Hämta sin egen data
				Styrelse = Hämta users för en viss organisation

				Read content
				Create content
				Delete content
		*/

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
/*
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
*/
		// Create new member
		$entity = new MemberModel;
//		$entity->member_number   = $member_number;
		$entity->email           = $json["email"]           ?? null;
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
		$entity->address_country = $json["address_country"] ?? "se";
		$entity->phone           = $json["phone"]           ?? null;
		$entity->created_at      = $json["created_at"]      ?? null;
		$entity->updated_at      = $json["updated_at"]      ?? null;

/*
		// Add relations
		if(!empty($json["relations"]))
		{
			$entity->addRelations($json["relations"]);
		}
*/
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
	function read(Request $request, $member_id)
	{
		// Load the entity
		$entity = MemberModel::load([
			"member_id" => $member_id
		]);

		// Generate an error if there is no such member
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "Could not find any member with specified member_id",
			], 404);
		}
		else
		{
			// Convert user object to array
			$result = $entity->toArray();

			// Get roles and permission for user
			$result["roles"] = [];
			$roles = DB::table("membership_roles")
				->join("membership_members_roles", "membership_members_roles.role_id", "membership_roles.role_id")
				->select("membership_roles.role_id", "membership_roles.group_id", "membership_roles.title", "membership_roles.description")
				->where("member_id", $member_id)
				->get();
			foreach($roles as $role)
			{
				$result["roles"][$role->role_id] = (array)$role;
				$result["roles"][$role->role_id]["permissions"] = DB::table("membership_permissions")->where("role_id", $role->role_id)->get();
			}

			// Send response to client
			return Response()->json([
				"data" => $entity->toArray(),
			], 200);
		}
	}

	/**
	 *
	 */
	function update(Request $request, $member_id)
	{
		// Load the entity
		$entity = MemberModel::load([
			"member_id" => ["=", $member_id]
		]);

		// Generate an error if there is no such member
		if(false === $entity)
		{
			return Response()->json([
				"status" => "error",
				"message" => "Could not find any member with specified member_id",
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

		// Send response to client
		return Response()->json([
			"status" => "updated",
			"data" => $entity->toArray(),
		], 200);
	}

	/**
	 *
	 */
	function delete(Request $request, $member_id)
	{
		// Load the entity
		$entity = MemberModel::load([
			"member_id" => ["=", $member_id]
		]);

		// Generate an error if there is no such member
		if(false === $entity)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Could not find any member with specified member_id",
			], 404);
		}

		if($entity->delete())
		{
			return Response()->json([
				"status"  => "deleted",
				"message" => "The member was successfully deleted",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "error",
				"message" => "An error occured when trying to delete member",
			], 500);
		}
	}

	/**
	 * Authenticate a user
	 */
	public function authenticate(Request $request)
	{
		$username = $request->get("username");
		$password = $request->get("password");

		// TODO: Validate input

		// Check if the user is in the database
		$result = DB::table("membership_members")
			->select("member_id", "password")
			->where("email", $username)
			->first();

		// Verify the password hash
		if($result && password_verify($password, $result->password))
		{
			return Response()->json([
				"member_id" => $result->member_id,
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "error",
				"message" => "The username and/or password you specified was incorrect",
			], 401);
		}
	}

	public function getGroups(Request $request)
	{
/*
		// TODO: Get roles from user
		$roles = [2, 5];

		// Get groups the where the user have a "view group" permission
		$this->_loadPermissions($roles);
		$groups = $this->_checkPermission("view group");
*/
		// Paging and permission filter
		$filters = [
			"per_page" => $this->per_page($request), // TODO: Rename?
//			"group_id" => ["in", $groups],
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
		//TODO
		return $result;
	}
}