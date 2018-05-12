<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Makeradmin\Traits\EntityStandardFiltering;

class Template extends Controller
{
	use EntityStandardFiltering;

	/**
	 * Return a list of all queued/sent messages
	 */
	public function list(Request $request)
	{
		$params = $request->query->all();
		return $this->_list("Template", $params);
	}

	/**
	 *
	 */
	public function create(Request $request)
	{
		$data = $request->json()->all();
		return $this->_create("Template", $data);
	}

	/**
	 * Load a queued/sent messages
	 */
	public function read(Request $request, $template_id)
	{
		return $this->_read("Template", [
			"template_id" => $template_id
		]);
	}

	/**
	 *
	 */
	public function update(Request $request, $template_id)
	{
		$data = $request->json()->all();
		return $this->_update("Template", [
			"template_id" => $template_id
		], $data);
	}

	/**
	 *
	 */
	public function delete(Request $request, $template_id)
	{
		return $this->_delete("Template", [
			"template_id" => $template_id
		]);
	}
}