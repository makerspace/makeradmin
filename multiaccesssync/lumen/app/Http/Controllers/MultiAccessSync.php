<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;
use App\Libraries\CurlBrowser;
use Illuminate\Support\Facades\Storage;

class MultiAccessSync extends Controller
{
	/**
	 * Cross-check databases and report differences
	 */
	public function diff(Request $request, $filename)
	{
		$curl = new CurlBrowser;

		// Process an already uploaded file
		if(!Storage::disk("uploads")->exists($filename))
		{
			// Send response to client
			return Response()->json([
				"message" => "The file $filename could not be found",
			], 404);
		}

		$data = Storage::disk("uploads")->get($filename);

		$xml = simplexml_load_string($data);

		// Go through all RFID keys
		$users = [];
		$member_numbers = [];
		foreach($xml->User as $user)
		{
			// Caste the name to a integer
			$member_number = (int)$user->name;

			// If casting failed, user string instead
			if($member_number == 0)
			{
				$member_number = (string)$user->name;
			}
			else
			{
				// If casting was successful, add to list of members we should load
				$member_numbers[] = $member_number;
			}

			// Save data in a new clean array
			$users[$member_number] = [
				"multiaccess_key" => [],
				"local_key" => [],
				"member" => [],
				"errors" => [],
			];


			// The name should not be empty
			if(empty($user->name))
			{
				$users[$member_number]["errors"][] = "The name should not be empty";
			}
/*
			// The tagid should not be empty
			if(empty($user->Card))
			{
				$users[$member_number]["errors"][] = "The tagid should not be empty";
			}
*/
			// Check customer name
			if($user->CustomerName != "Stockholm Makerspace")
			{
				$users[$member_number]["errors"][] = "Customer should be \"Stockholm Makerspace\"";
			}

			// Check permissions
			if(!$this->_checkPermissions($user))
			{
				$users[$member_number]["errors"][] = "Något verkar vara fel med personens behörigheter";
			}

			if($d = strtotime((string)$user->Start))
			{
				$startdate = date("Y-m-d\TH:i:s\Z", $d);
			}
			else
			{
				$startdate = null;
			}

			if($d = strtotime((string)$user->Stop))
			{
				$enddate = date("Y-m-d\TH:i:s\Z", $d);
			}
			else
			{
				$enddate = null;
			}

			// Save data in a new clean array
			$users[$member_number]["multiaccess_key"] = [
				"member_number" => $member_number,
				"tagid"         => (string)$user->Card,
				"active"        => (bool) ($user->pulBlock == 0),
				"startdate"     => $startdate,
				"enddate"       => $enddate,
			];
		}

		// Get all members in xml file from API
		$curl->call("GET", "http://" . config("service.gateway") . "/membership/member", [
			"member_number" => implode(", ", $member_numbers),
			"per_page" => 5000,
		]);
		foreach($curl->GetJson()->data as $member)
		{
			$users[$member->member_number]["member"] = (array)$member;
		}

		// Get all relations to keys from API
		$curl->call("GET", "http://" . config("service.gateway") . "/relations", [
			"param" => "/membership/member/%",
			"matchUrl" => "/keys/(.*)",
		]);

		// Go through all relations and merge them into the $users table
		$member_ids = [];
		$key_ids = [];
		$relations = [];
		foreach($curl->GetJson()->data as $relation)
		{
			$member_id = substr($relation->url, 19);
			$key_id    = $relation->matches[1];
			$relations[$key_id] = $member_id;
			$member_ids[] = $member_id;
			$key_ids[] = $key_id;
		}

		// Get all members in local database from API
		$curl->call("GET", "http://" . config("service.gateway") . "/membership/member", [
			"entity_id" => implode(", ", $member_ids),
			"per_page" => 5000,
		]);
		$member_number_mapping = [];
		foreach($curl->GetJson()->data as $member)
		{
			$users[$member->member_number]["member"] = (array)$member;
			$member_number_mapping[$member->member_id] = $member->member_number;
		}

		// Get all keys from API
		$curl->call("GET", "http://" . config("service.gateway") . "/keys", [
			"per_page" => 5000,
		]);

		foreach($curl->GetJson()->data as $key)
		{
			if(empty($users[$member_number]["multiaccess_key"]))
			{
				$users[$member_number]["multiaccess_key"] = [];
				$users[$member_number]["errors"] = [];
			}

			if(array_key_exists($key->key_id, $relations))
			{
				// There is a member connected to the key
				if(array_key_exists($relations[$key->key_id], $member_number_mapping))
				{
					$member_number = $member_number_mapping[$relations[$key->key_id]];
					$users[$member_number]["local_key"] = $key;
					if(empty($users[$member_number]["member"]))
					{
						$users[$member_number]["member"] = [];
					}
				}
			}
			else
			{
				// There is no member connected to the key
				$users["key_{$key->tagid}"] = [
					"local_key" => $key,
					"errors" => [],
					"member" => [],
				];

				if(empty($users["key_{$key->tagid}"]["multiaccess_key"]))
				{
					$users["key_{$key->tagid}"]["multiaccess_key"] = [];
				}
			}
		}

		// Send response to client
		return Response()->json([
			"data" => array_values($users),
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

	/**
	 * Upload an *.xml export from MultiAccess
	 */
	public function upload(Request $request)
	{
		// Check that the upload was okay
		$file = $request->file("files")[0];
		if($file->isValid())
		{
			// Store the uploaded file
			$data = file_get_contents((string)$file);
			$filename = date("Y-m-d\TH:i:s\Z").".xml";
			Storage::disk("uploads")->put($filename, $data);

			// Send response to client
			return Response()->json([
				"data" => [
					"filename" => $filename,
				],
			], 201);
		}
		else
		{
			return Response()->json([
				"status" => "error",
				"message" => "Error uploading file",
			], 500);
		}
	}
}