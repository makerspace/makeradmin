<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Makeradmin\Traits\EntityStandardFiltering;

class Permission extends Controller
{
	use EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request)
	{
		$params = $request->query->all();
		return $this->_list("Permission", $params);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$data = $request->json()->all();
		return $this->_create("Permission", $data);
	}

	/**
	 *
	 */
	function read(Request $request, $permission_id)
	{
		return $this->_read("Permission", [
			"permission_id" => $permission_id
		]);
	}

	/**
	 *
	 */
	function update(Request $request, $permission_id)
	{
		$data = $request->json()->all();
		return $this->_update("Permission", [
			"permission_id" => $permission_id
		], $data);
	}

	/**
	 *
	 */
	function delete(Request $request, $permission_id)
	{
		return $this->_delete("Permission", [
			"permission_id" => ["=", $permission_id]
		]);
	}

	/**
	 *
	 */
	function batchRegister(Request $request)
	{
		$data = $request->json()->all();
		$permissions = array_unique(explode(',',$data['permissions']), SORT_STRING);
		// TODO: What status should be returned if no permissions were given?
		if(count($permissions) === 0) {
			// Send response to client
			return Response()->json([
				"status" => "ok",
			], 200);
		}

		// When count($permissions)==2 the first element is expected to be an operator (eg '=' or '<>')
		// TODO: Fix underlying problem in Makeradmin\Models\Entity.php 
		if (count($permissions) == 2) {
			$permissions[] = $permissions[0];
		}
		$result = $this->_list("Permission", [
			'permission' => $permissions, 
			'per_page' => count($permissions)]);

		$existing_permission = array_map(function($obj){
			return $obj->permission;}, $result->getData()->data);

		$succeeded = [];
		$failed = [];
		$add_permissions = array_diff($permissions, $existing_permission);
		foreach($add_permissions as $permission){
			$response = $this->_create("Permission", [
				'permission' => $permission,
				'role_id' => 1,
			]);
			if ($response->getStatusCode() == 201) {
				$succeeded[] = $permission;
			} else {
				$failed[] = $permission;
			}
		}

		// TODO: Should return error when any permission failed
		return Response()->json([
			"status" => "created",
			"data" => [
				'succeeded' => $succeeded,
				'failed' => $failed,
			],
		], 201);
		
	}
}