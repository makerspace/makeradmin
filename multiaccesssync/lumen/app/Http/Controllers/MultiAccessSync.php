<?php

namespace App\Http\Controllers;

class MultiAccessSync extends Controller
{
	/**
	 *
	 */
	public function __construct()
	{
	}

	/**
	 * Cross-check databases and report differences
	 */
	public function index()
	{
		// TODO: Receive uploaded file
		$data = utf8_encode(file_get_contents("/var/www/html/public/users.xml"));

		echo "<pre>";

		$xml = simplexml_load_string($data);

		// Go through all RFID keys
		$users = [];
		$user_ids = [];
		$errors = [];
		foreach($xml->User as $user)
		{
			// The name should not be empty
			if(empty($user->name))
			{
				$errors[(string)$user->name]["messages"][] = "The name should not be empty";
			}

			// The tagid should not be empty
			if(empty($user->Card))
			{
				$errors[(string)$user->name]["messages"][] = "The tagid should not be empty";
			}

			// Check that there is not start date
			if(isset($user->Start))
			{
				$errors[(string)$user->name]["messages"][] = "Should not have an startdate";
			}

			// Check that all tags ar active
			if($user->pulBlock != "0")
			{
				$errors[(string)$user->name]["messages"][] = "The tag is not activated";
			}

			// Check customer name
			if($user->CustomerName != "Stockholm Makerspace")
			{
				$errors[(string)$user->name]["messages"][] = "Customer should be \"Stockholm Makerspace\"";
			}

			// Check permissions
			if(!$this->_checkPermissions($user))
			{
				$errors[(string)$user->name]["messages"][] = "Something is wrong with the permissions";
			}

			// Save data in a new clean array
			$users[] = [
				"member_number" => (string)$user->name,
				"tagid"         => (string)$user->Card,
				"enddate"       => (string)$user->Stop,
			];
			$user_ids[] = (string)$user->name;
		}

		// TODO: Batch process 100 at a time

		// TODO: Get all members from API
		$x = implode(", ", $user_ids);
		echo "TODO: Get users in ({$x})\n";
		// TODO: Error reporting if someone is not found

		// Compare data
		// TODO: Get tags
		$tags = [];
		foreach($tags as $user)
		{
			// TODO: Compare end date
			if($user->enddate != $users[$user->member_number]["enddate"])
			{
				$errors[$user->member_number]["messages"][] = "The enddate is wrong";
			}

			// TODO: Compare tagid
			if($user->tagid != $users[$user->member_number]["tagid"])
			{
				$errors[$user->member_number]["messages"][] = "The tagid is wrong";
			}
		}

print_r($errors);
print_r($users);
die();

		return Response()->json([
			"hai" => "lol",
			"data" => $xml,
		], 200);
	}

	/**
	 * Check that the key have the correct permissions
	 */
	protected function _checkPermissions($user)
	{
		// The user does only have the "Member" permissions
		if(
			$user->Authorities->Authority->count() == 1 &&
			$user->Authorities->Authority[0]->Name == "DKV 53 Stockholm Makerspace - Medlem" &&
			$user->Authorities->Authority[0]->Start == "" &&
			$user->Authorities->Authority[0]->Stop == "" &&
			$user->Authorities->Authority[0]->Blocked == 0
		)
		{
			return true;
		}

		// The user has both "Member" and "Styrelsen" permission
		if(
			$user->Authorities->Authority->count() == 2 &&
			$user->Authorities->Authority[0]->Name == "DKV 53 Stockholm Makerspace - Medlem" &&
			$user->Authorities->Authority[0]->Start == "" &&
			$user->Authorities->Authority[0]->Stop == "" &&
			$user->Authorities->Authority[0]->Blocked == 0 &&
			$user->Authorities->Authority[1]->Name == "DKV 53 Stockholm Makerspace - Styrelsen" &&
			$user->Authorities->Authority[1]->Start == "" &&
			$user->Authorities->Authority[1]->Stop == "" &&
			$user->Authorities->Authority[1]->Blocked == 0
		)
		{
			return true;
		}

		// The user has both "Member" and "Styrelsen" permission - reverse direction
		if(
			$user->Authorities->Authority->count() == 2 &&
			$user->Authorities->Authority[0]->Name == "DKV 53 Stockholm Makerspace - Styrelsen" &&
			$user->Authorities->Authority[0]->Start == "" &&
			$user->Authorities->Authority[0]->Stop == "" &&
			$user->Authorities->Authority[0]->Blocked == 0 &&
			$user->Authorities->Authority[1]->Name == "DKV 53 Stockholm Makerspace - Medlem" &&
			$user->Authorities->Authority[1]->Start == "" &&
			$user->Authorities->Authority[1]->Stop == "" &&
			$user->Authorities->Authority[1]->Blocked == 0
		)
		{
			return true;
		}

		return false;
	}
}