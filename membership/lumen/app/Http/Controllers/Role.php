<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Makeradmin\Traits\EntityStandardFiltering;

class Role extends Controller
{
	use EntityStandardFiltering;

	/**
	 *
	 */
	function list(Request $request)
	{
		$params = $request->query->all();
		return $this->_list("Role", $params);
	}

	/**
	 *
	 */
	function create(Request $request)
	{
		$data = $request->json()->all();
		return $this->_create("Role", $data);
	}

	/**
	 *
	 */
	function read(Request $request, $role_id)
	{
		return $this->_read("Role", [
			"role_id" => $role_id
		]);
	}

	/**
	 *
	 */
	function update(Request $request, $role_id)
	{
		$data = $request->json()->all();
		return $this->_update("Role", [
			"role_id" => $role_id
		], $data);
	}

	/**
	 *
	 */
	function delete(Request $request, $role_id)
	{
		return $this->_delete("Role", [
			"role_id" => ["=", $role_id]
		]);
	}
}