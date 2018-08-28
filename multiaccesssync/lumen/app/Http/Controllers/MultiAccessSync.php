<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Makeradmin\Libraries\CurlBrowser;
use Illuminate\Support\Facades\Storage;

class MultiAccessSync extends Controller
{
	protected function read_XML(string $string)
	{
		$xml_data = simplexml_load_string($string);
		$users_data = [];
		foreach ($xml_data->User as $user)
		{
			// Cast the name to a integer
			$member_number = (int)$user->name;
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
			
			$user_data = [
				"member_number" => $member_number,
				"tagid"         => (string)$user->Card,
				"blocked"        => (bool) ($user->pulBlock == 0),
				"startdate"     => $startdate,
				"enddate"       => $enddate,
				"errors" => [],
			];
			
			// If casting failed, user string instead
			if($member_number == 0)
			{
				$user_data["member_number"] = (string)$user->name;
				// The name should not be empty
				$user_data["errors"][] = "The name should not be empty";
			}
			/*
			 // The tagid should not be empty
			 if(empty($user->Card))
			 {
			 $user_data["errors"][] = "The tagid should not be empty";
			 }
			 */
			// Check customer name
			if($user->CustomerName != "Stockholm Makerspace")
			{
				$user_data["errors"][] = "Customer should be \"Stockholm Makerspace\"";
			}
			
			// Check permissions
			/*
			 if(!$this->_checkPermissions($user))
			 {
			 $user_data["errors"][] = "Något verkar vara fel med personens behörigheter";
			 }
			 */
			$users_data[] = $user_data;
		}
		return $users_data;
	}

	protected function read_json(string $string)
	{
		$data = json_decode($string);
		$users_data = [];
		foreach ($data as $user)
		{
			// Cast the name to a integer
			
			$member_number = (int)($user->member_number);
/*			if($d = strtotime((string)$user->start_timestamp)) {
				$startdate = date("Y-m-d\TH:i:s\Z", $d);
			} else {
				$startdate = null;
			}
			*/
			$startdate = null;
			if($d = strtotime((string)$user->end_timestamp)) {
				$enddate = date("Y-m-d\TH:i:s\Z", $d);
			} else {
				$enddate = null;
			}
			$user_data = [
				"member_number" => $member_number,
				"tagid"         => (string)$user->rfid_tag,
				//"active"        => (bool) $user->status,
				"startdate"     => $startdate,
				"enddate"       => $enddate,
				"errors" => [],
			];
			
			// If casting failed, user string instead
			if($member_number == 0)
			{
				$user_data["member_number"] = (string)$user->member_number;
				$user_data["errors"][] = "The name should not be empty";
			}

			// The tagid should not be empty
			if(empty($user->rfid_tag))
			{
				$user_data["errors"][] = "The tagid should not be empty";
			}
			
			$users_data[] = $user_data;
		}
		return $users_data;
	}
	
	/**
	 * Cross-check databases and report differences
	 */
	public function diff(Request $request, $filename)
	{
		$curl = new CurlBrowser;
		$curl->setHeader("Authorization", "Bearer " . config("service.bearer"));

		// Process an already uploaded file
		if(!Storage::disk("uploads")->exists($filename))
		{
			// Send response to client
			return Response()->json([
				"message" => "The file $filename could not be found",
			], 404);
		}

		$data = Storage::disk("uploads")->get($filename);

		$file_ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
		$multiaccess_user_data = [];
		if($file_ext == "xml") {
			$multiaccess_user_data = $this->read_XML($data);
		} elseif ($file_ext == "json") {
			$multiaccess_user_data = $this->read_json($data);
		}

		// Go through all RFID keys
		$users = [];
		$member_numbers = [];
		foreach($multiaccess_user_data as $user)
		{
			$member_number = $user["member_number"];

			// If member_number is an int, add to list of members we should load
			if (is_int($member_number))
			{
				$member_numbers[] = $member_number;
			}
			$user_data_errors = $user["errors"];
			unset($user["errors"]);

			// Save data in a new clean array
			$users[$member_number] = [
				"multiaccess_key" => $user,
				"local_key" => [],
				"member" => [],
				"errors" => $user_data_errors,
			];
		}

		// Get all members in data file from API
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
			$current_member = [];
			$member_data = (array)$member;
			if (!empty($member)) {
				$current_member["member_id"] = $member_data["member_id"];
				$current_member["member_number"] = $member_data["member_number"];
				$current_member["firstname"] = $member_data["firstname"];
				$current_member["lastname"] = $member_data["lastname"];
				//$current_member["key_id"] = $member_data["key_id"];
				//$current_member["rfid_tag"] = $member_data["tagid"];
				//$current_member["status"] = $member_data["status"];
				//$current_member["end_timestamp"] = $member_data["enddate"];
			}
			$users[$member->member_number]["member"] = $current_member;
			$member_number_mapping[$member->member_id] = $member->member_number;
			if(!array_key_exists("local_key", $users[$member->member_number]))
			{
				$users[$member->member_number]["local_key"] = [];
			}
			if(!array_key_exists("multiaccess_key", $users[$member->member_number]))
			{
				$users[$member->member_number]["multiaccess_key"] = [];
			}
			if(!array_key_exists("errors", $users[$member->member_number]))
			{
				$users[$member->member_number]["errors"] = [];
			}
			
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
	 *
	 */
	public function dumpmembers(Request $request)
	{
		$curl = new CurlBrowser;
		$curl->setHeader("Authorization", "Bearer " . config("service.bearer"));

		// Get all keys
		$curl->call("GET", "http://" . config("service.gateway") . "/membership/key", [
			"per_page" => 5000,
		]);
		$keys = $curl->GetJson()->data;

		// Get all members with keys
		$curl->call("GET", "http://" . config("service.gateway") . "/membership/member", [
			'include_membership' => true,
			"per_page" => 5000,
		]);

		$key_members = $curl->GetJson()->data;

		$member_keys = [];
		foreach ($key_members as $member) {
			$current_member = [];
			$member_id = (int) $member->member_id;
			assert($member_id !== 0);
			$member_number = (int) $member->member_number;
			assert($member_number !== 0);

			$current_member['member_id'] = $member_id;
			$current_member['member_number'] = $member_number;
			$current_member['firstname'] = $member->firstname;
			$current_member['lastname'] = $member->lastname;
			$current_member['end_date'] = $member->membership->labaccess_end;
			$current_member['keys'] = [];
			$member_keys[$member_id] = $current_member;
		}

		foreach ($keys as $key) {
			$member_id = $key->member_id;
			if (array_key_exists($member_id, $member_keys)) {
				$current_key = [
					'key_id' => $key->key_id,
					'rfid_tag' => $key->tagid,
				];
				$member_keys[$member_id]['keys'][] = $current_key;
			} else {
				error_log("Key ".$key->key_id." has invalid member");
			}
		}

		// Send response to client
		return Response()->json([
			"data" => array_values($member_keys),
		], 200);
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
			$file_ext = ".json";
			if(strtolower(substr($data,0,5))=="<?xml")
			{
				$file_ext = ".xml";
			}
			$filename = date("Y-m-d\TH:i:s\Z").$file_ext;
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
