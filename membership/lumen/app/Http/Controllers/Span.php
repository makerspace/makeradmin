<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Makeradmin\Traits\EntityStandardFiltering;

class Span extends Controller
{
	use EntityStandardFiltering;

	/**
	 *
	 */
	public function list(Request $request)
	{
		$params = $request->query->all();
		return $this->_list("Span", $params);
	}

	/**
	 *
	 */
	public function create(Request $request)
	{
		$data = $request->json()->all();
		return $this->_create("Span", $data);
	}

	/**
	 * Create new span for member
	 */
	public function create_entity($data)
	{
		return $this->_create("Span", $data);
	}

	/**
	 *
	 */
	public function read(Request $request, $span_id)
	{
		$params = $request->query->all();
		$params['span_id'] = $span_id;
		return $this->_read("Span", $params);
	}

	/**
	 *
	 */
	public function update(Request $request, $span_id)
	{
		$data = $request->json()->all();
		return $this->_update("Span", [
			"span_id" => $span_id
		], $data);
	}

	/**
	 *
	 */
	public function delete(Request $request, $span_id)
	{
		return $this->_delete("Span", [
			"span_id" => $span_id
		]);
	}
}