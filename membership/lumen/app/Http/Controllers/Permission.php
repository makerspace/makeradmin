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
}