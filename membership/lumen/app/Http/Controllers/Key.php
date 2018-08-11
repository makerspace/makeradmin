<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Makeradmin\Traits\EntityStandardFiltering;

class Key extends Controller
{
	use EntityStandardFiltering;

	/**
	 *
	 */
	public function list(Request $request)
	{
		$params = $request->query->all();
		return $this->_list("Key", $params);
	}

	/**
	 *
	 */
	public function create(Request $request)
	{
		$data = $request->json()->all();
		return $this->_create("Key", $data);
	}

	/**
	 *
	 */
	public function read(Request $request, $key_id)
	{
		return $this->_read("Key", [
			"key_id" => $key_id
		]);
	}

	/**
	 *
	 */
	public function update(Request $request, $key_id)
	{
		$data = $request->json()->all();
		return $this->_update("Key", [
			"key_id" => $key_id
		], $data);
	}

	/**
	 *
	 */
	public function delete(Request $request, $key_id)
	{
		return $this->_delete("Key", [
			"key_id" => $key_id
		]);
	}
}