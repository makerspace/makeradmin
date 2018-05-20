<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Member as MemberModel;
use App\Models\Group as GroupModel;

use Makeradmin\Traits\EntityStandardFiltering;

use DB;

class Member extends Controller
{
	use EntityStandardFiltering;

	/**
	 *
	 */
	public function list(Request $request)
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
			En header specificerar vilken organisation/grupp man arbetar mot
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

		// Get all query string parameters
		$params = $request->query->all();

		// Filter on member_number's
		if(!empty($params["member_number"]))
		{
			// Explode the list of id's
			$params["member_number"] = explode(",", $params["member_number"]);
		}

		return $this->_list("Member", $params);
	}

	/**
	 *
	 */
	public function create(Request $request)
	{
		$json = $request->json()->all();

		// TODO: This should be removed
		if(!empty($json["member_number"]))
		{
			$member_number = $json["member_number"];
		}
		else
		{
			// Create a unique member number if not specified
			$newest_member = MemberModel::load([
				["sort", ["member_number", "desc"]]
			]);

			if(empty($newest_member))
			{
				$member_number = 1000;
			}
			else
			{
				$member_number = ($newest_member->member_number + 1);
			}
		}

		// Create new member
		$entity = new MemberModel;
		$entity->member_number   = $member_number;
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

		if ($json["unhashed_password"]) {
			$entity->password = password_hash($entity->password, PASSWORD_DEFAULT);
		}

		error_log($entity->password);
		error_log($json["password"]);
		if(@$json["created_at"] !== null)
		{
			$entity->created_at = $json["created_at"];
		}
		if(@$json["updated_at"] !== null)
		{
			$entity->updated_at = $json["updated_at"];
		}

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		// Get member_id
		$member_id = $entity->entity_id;

		// Add member to groups
		if(!empty($json["groups"]))
		{
			foreach($json["groups"] as $group)
			{
				$group_id = DB::table("membership_groups")
					->where("name", "=", $group["name"])
					->value("group_id");

				if(!$group_id)
				{
					return Response()->json([
						"status" => "error",
						"message" => "No group found with name {$group["name"]}",
					], 404);
				}

				DB::insert("REPLACE INTO membership_members_groups(member_id, group_id) VALUES(?, ?)", [$member_id, $group_id]);
			}
		}

		// Send response to client
		return Response()->json([
			"status" => "created",
			"data" => $entity->toArray(),
		], 201);
	}

	/**
	 *
	 */
	public function read(Request $request, $member_id)
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
	public function update(Request $request, $member_id)
	{
		$data = $request->json()->all();
		return $this->_update("Member", [
			"member_id" => $member_id
		], $data);
	}

	/**
	 *
	 */
	public function delete(Request $request, $member_id)
	{
		return $this->_delete("Member", [
			"member_id" => $member_id,
		]);
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
				"data" => [
					"member_id" => $result->member_id,
				]
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

	/**
	 * Get a list of groups of the member
	 */
	public function getGroups(Request $request, $member_id)
	{
		// Get all query string parameters
		$params = $request->query->all();

		// Filter on member
		$params["member_id"] = $member_id;

		return $this->_list("Group", $params);
	}

	/**
	 * Add a group to a member
	 */
	public function addGroup(Request $request, $member_id)
	{
		$json = $request->json()->all();

		// Add the group to the user
		$data = [];
		foreach($json["groups"] as $group_id)
		{
			DB::insert("REPLACE INTO membership_members_groups(member_id, group_id) VALUES(?, ?)", [$member_id, $group_id]);
		}

		return Response()->json([
			"status"  => "ok",
		], 200);
	}

	/**
	 * Remove a group from a member
	 */
	public function removeGroup(Request $request, $member_id)
	{
		$json = $request->json()->all();

		// Add the group to the user
		$data = [];
		foreach($json["groups"] as $group_id)
		{
			DB::insert("DELETE FROM membership_members_groups WHERE member_id = ? AND group_id = ?", [$member_id, $group_id]);
		}

		return Response()->json([
			"status"  => "ok",
		], 200);
	}
}
