<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Traits\EntityStandardFiltering;

//use App\Libraries\CurlBrowser;

class Recipient extends Controller
{
	use EntityStandardFiltering;

	/**
	 * Return a list of all queued/sent messages
	 */
	public function list(Request $request, $message_id)
	{
		$params = $request->query->all();

		// Filter recipients on message_id
		$params["message_id"] = $message_id;

		return $this->_list("Recipient", $params);
	}

	/**
	 * Return a list of all messages sent to a specific user
	 */
	public function userlist(Request $request, $member_id)
	{
		$params = $request->query->all();

		// Filter recipients on member_id
		$params["member_id"] = $member_id;

		return $this->_list("Recipient", $params);
	}
}