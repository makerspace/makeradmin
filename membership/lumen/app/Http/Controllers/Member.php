<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Member as MemberModel;
use App\Models\Group as GroupModel;
use App\Models\Span as SpanModel;

use Makeradmin\Traits\EntityStandardFiltering;
use Makeradmin\Exceptions\EntityValidationException;

use DB;

const SPAN_LABACCESS = "labaccess";
const SPAN_MEMBERSHIP = "membership";
const SPAN_SPECIAL_LABACCESS = "special_labaccess";

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

		$include_membership = empty($params["include_membership"]) ? false : filter_var($params["include_membership"], FILTER_VALIDATE_BOOLEAN);
		
		unset($params["include_membership"]);

		$response = $this->_list("Member", $params);

		if (!empty($include_membership) && $include_membership) {
			// Modify the response to include membership data
			$result = $response->getData()->data;
			foreach ($result as $user) {
				$user->membership = $this->_getMembership($user->member_id);
			}
			return Response()->json([
				"status" => "ok",
				"data" => $result,
			], 200);
		} else {
			return $response;
		}
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

		if (isset($json["unhashed_password"]) && $json["unhashed_password"]) {
			$entity->password = password_hash($entity->password, PASSWORD_DEFAULT);
		}

		if(@$json["created_at"] !== null)
		{
			$entity->created_at = $json["created_at"];
		}
		if(@$json["updated_at"] !== null)
		{
			$entity->updated_at = $json["updated_at"];
		}
		if (isset($json["create_deleted"]) && $json["create_deleted"] === true) {
			$entity->deleted_at = $entity->created_at ?? DB::raw("NOW()");
			$entity->include_deleted_at();
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

		// Load the entity again before we return it.
		// This is required to make sure things like created_at are set properly
		// (as that field is set by the database, not in php)
		$filters = (array)$request->query->all();
		$filters['member_id'] = $member_id;
		$entity = MemberModel::load($filters);

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
		$filters = (array)$request->query->all();
		$filters['member_id'] = $member_id;
		$entity = MemberModel::load($filters);

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

			// Get groups and permission for user
			// TODO: Groups are arranged into a hierarchy which should be expanded
			$result["groups"] = [];
			$groups = DB::table("membership_members_groups")
				->join("membership_groups", "membership_groups.group_id", "membership_members_groups.group_id")
				->select("membership_groups.group_id", "membership_groups.parent", "membership_groups.name", "membership_groups.title")
				->where("member_id", $member_id)
				->get();
			foreach($groups as $group)
			{
				$group_id = $group->group_id * 1;
				$result["groups"][$group_id] = (array)$group;
				$group_permissions = DB::table("membership_permissions")
					->join("membership_group_permissions", "membership_group_permissions.permission_id", "membership_permissions.permission_id")
					->where("membership_group_permissions.group_id", $group->group_id)
					->pluck("permission")
					->all();
				$result["groups"][$group_id]["permissions"] = $group_permissions;
			}

			// Send response to client
			return Response()->json([
				"data" => $result,
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

	public function activate(Request $request, $member_id)
	{
		DB::table("membership_members")
			->where("member_id", $member_id)
			->update(["deleted_at" => null]);

		return Response()->json([
			"status"  => "activated",
			"message" => "The member was successfully activated",
		], 200);
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
			->whereNull('deleted_at')
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

	/**
	 * Get all permissions for a member
	 */
	public function getKeys(Request $request, $member_id)
	{
		// Get all query string parameters
		$params = $request->query->all();

		// Filter on member
		$params["member_id"] = $member_id;
		return $this->_list("Key", $params);
	}

	/**
	 * Get all permissions for a member
	 */
	public function getPermissions(Request $request, $member_id)
	{
		// Get permissions for user
		// TODO: Groups are arranged into a hierarchy which should be expanded
		$permissions = DB::table("membership_members_groups")
			->join("membership_group_permissions", "membership_group_permissions.group_id", "membership_members_groups.group_id")
			->join("membership_permissions", "membership_permissions.permission_id", "membership_group_permissions.permission_id")
			->where('member_id', $member_id)
			->distinct()
			->select('membership_group_permissions.permission_id','permission')
			->get();

		// Send response to client
		return Response()->json([
			"data" => $permissions,
		], 200);
	}

	public function addMembershipSpan(Request $request, $member_id)
	{
		$json = $request->json()->all();

		if ($json['type'] != SPAN_LABACCESS && $json['type'] != SPAN_MEMBERSHIP && $json['type'] != SPAN_SPECIAL_LABACCESS) {
			return Response()->json([
				"status"  => "error",
				"message" => "Unknown membership type {$json['type']}",
			], 400);
		}

		$span_data = [
			'member_id' => $member_id,
			'startdate' => $json['startdate'],
			'enddate' => $json['enddate'],
			'span_type' => $json['type'],
			'creation_reason' => $json['creation_reason'],
		];

		try {
			$this->_create_span($span_data);
		} catch (EntityValidationException $e) {
			if ($e->getType() == 'unique' && $e->getColumn() == 'creation_reason'){
				$old_span = SpanModel::load(['creation_reason' => $json['creation_reason']], false);
				if (
					$old_span->member_id == $span_data['member_id'] &&
					$old_span->startdate == $span_data['startdate'] &&
					$old_span->enddate == $span_data['enddate'] &&
					$old_span->span_type == $span_data['span_type']
				) {
					// TODO: Report already exists?
				} else {
					return Response()->json([
						"status" => "error",
						"message" => "Span with creation_reason {$json['creation_reason']} already exists"
					], 400);
				}
			} else {
				throw $e;
			}
		}

		return $this->getMembership($request, $member_id);
	}

	public function addMembershipDays(Request $request, $member_id)
	{
		$json = $request->json()->all();
		if (empty($json['type'])) {
			return Response()->json([
				"status"  => "error",
				"message" => "Missing parameter 'type' (" . SPAN_LABACCESS . ", " . SPAN_MEMBERSHIP . ", " . SPAN_SPECIAL_LABACCESS . ")",
			], 400);
		}

		if (empty($json['days'])) {
			return Response()->json([
				"status"  => "error",
				"message" => "Missing parameter 'days'",
			], 400);
		}

		if (empty($json['creation_reason']) || $json['creation_reason'] == null) {
			return Response()->json([
				"status"  => "error",
				"message" => "Missing parameter 'creation_reason'",
			], 400);
		}

		$last_period = DB::table("membership_spans")
			->where('member_id', $member_id)
			->where('type', $json['type'])
			->whereNull('deleted_at')
			->max('enddate');

		if ($last_period == null || date_create_from_format('Y-m-d', $last_period) < date_create()) {
			$last_period = date("Y-m-d");
		}

		$days = (int)$json['days'];
		if ($days <= 0) {
			return Response()->json([
				"status"  => "error",
				"message" => "Must specify a positive number of days",
			], 400);
		}

		$endtime = date('Y-m-d', strtotime("+{$days} days", strtotime($last_period)));

		if ($json['type'] != SPAN_LABACCESS && $json['type'] != SPAN_MEMBERSHIP && $json['type'] != SPAN_SPECIAL_LABACCESS) {
			return Response()->json([
				"status"  => "error",
				"message" => "Unknown membership type {$json['type']}",
			], 400);
		}

		$span_data = [
			'member_id' => $member_id,
			'startdate' => $last_period,
			'enddate' => $endtime,
			'span_type' => $json['type'],
			'creation_reason' => $json['creation_reason'],
		];

		try {
			$this->_create_span($span_data);
		} catch (EntityValidationException $e) {
			if ($e->getType() == 'unique' && $e->getColumn() == 'creation_reason'){
				$old_span = SpanModel::load(['creation_reason' => $json['creation_reason']], false);
				$old_start = \DateTime::createFromFormat ('Y-m-d', $old_span->startdate);
				$old_duration = \DateTime::createFromFormat ('Y-m-d', $old_span->enddate)->diff($old_start);
				if (
					$old_span->member_id == $span_data['member_id'] &&
					$old_duration->d == $days && 
					$old_span->span_type == $span_data['span_type']
				) {
					// TODO: Report already exists?
				} else {
					return Response()->json([
						"status"  => "error",
						"message" => "Different span with same creation_reason {$json['creation_reason']} already exists, old days {$old_duration->days}",
					], 400);
				}
			} else {
				throw $e;
			}
		}
		return $this->getMembership($request, $member_id);
	}

	/**
	 * Create new span
	 */
	private function _create_span($span_data){
		$fields = ['member_id','startdate','enddate','span_type','creation_reason'];
		$entity = new SpanModel();
		foreach ($fields as $field) {
			$entity->{$field} = $span_data[$field] ?? null;
		}
		// Validate input
		$entity->validate();
		// Save entity
		return $entity->save();
	}

	/**
	 * Get membership times
	 */
	private function _getMembership($member_id)
	{
		$today = date("Y-m-d");

		// Check if the current time is covered by any span of valid membership times
		$labaccess = DB::table("membership_spans")
			->where('member_id', $member_id)
			->whereIn("type", [SPAN_LABACCESS, SPAN_SPECIAL_LABACCESS])
			->whereDate("startdate", "<=", $today)
			->whereDate("enddate", ">=", $today)
			->whereNull("deleted_at")
			->value('enddate') !== null;

		$membership = DB::table("membership_spans")
			->where('member_id', $member_id)
			->where("type", SPAN_MEMBERSHIP)
			->whereDate("startdate", "<=", $today)
			->whereDate("enddate", ">=", $today)
			->whereNull("deleted_at")
			->value('enddate') !== null;

		// Find the latest enddate of any membership span.
		// This is the time the member's membership ends.
		// (at least unless someone has been manually tweaking the database to create some sort of gap before that time)
		$labaccess_time = DB::table("membership_spans")
			->where('member_id', $member_id)
			->whereIn("type", [SPAN_LABACCESS, SPAN_SPECIAL_LABACCESS])
			->whereNull("deleted_at")
			->max("enddate");

		$membership_time = DB::table("membership_spans")
			->where('member_id', $member_id)
			->where("type", SPAN_MEMBERSHIP)
			->whereNull("deleted_at")
			->max("enddate");

		// Send response to client
		return [
			"has_labaccess" => $labaccess,
			"has_membership" => $membership,
			"labaccess_end" => $labaccess_time,
			"membership_end" => $membership_time,
		];
	}

	/**
	 * Get membership times
	 */
	public function getMembership(Request $request, $member_id)
	{
		// Send response to client
		return Response()->json([
			"status"  => "ok",
			"data" => $this->_getMembership($member_id),
		], 200);
	}

}
