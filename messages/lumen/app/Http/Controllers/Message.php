<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Models\Message as MessageModel;
use App\Models\Recipient as RecipientModel;

use App\Traits\Pagination;
use App\Traits\EntityStandardFiltering;

use App\Libraries\CurlBrowser;

class Message extends Controller
{
	use Pagination, EntityStandardFiltering;

	/**
	 * Return a list of all queued/sent messages
	 */
	function list(Request $request)
	{
		return $this->_applyStandardFilters("Message", $request);
	}

	/**
	 * Send a new message
	 */
	function create(Request $request)
	{
		// TODO: Get the chunk size from configuration
		$chunkSize = 2500;

		// TODO: Validate
		//   $json["recipients"][$i]["type"] == member|group
		//   $json["recipients"][$i]["id"] is existing
		//   $json["message_type"]
		//   $json["subject"] null if sms or not null if e-mail
		//   $json["body"]
		$json = $request->json()->all();

		// Load all members / groups from the API and put together in an distinct list (no duplicates)
		$recipientList = [];
		$memberIds = [];
		foreach($json["recipients"] as $recipient)
		{
			// Load the recipient
			if($recipient["type"] == "member")
			{
				// Save them in an array and batch process them
				$memberIds[] = $recipient["id"];
			}
			else if($recipient["type"] == "group")
			{
				// If the recipient is a group, get group list from API
				$ch = new CurlBrowser;
				// TODO: Gateway from config
				$result = $ch->call("GET", "http://makeradmin-apigateway/membership/group/{$recipient["id"]}/members?per_page={$chunkSize}");

				// Send an error message if the API request was unsuccessful
				if($ch->getStatusCode() != 200)
				{
					return Response()->json([
						"status" => "error",
						"message" => "An unexpected error occured while trying to load data from the membership module",
					], 502);
				}

				// Add the members to the recipient list
				foreach($ch->getJson()->data as $member)
				{
					$recipientList[$member->member_id] = $member;
				}
			}
		}

		// Batch process members
		foreach(array_chunk($memberIds, $chunkSize) as $chunk)
		{
			$str_ids = implode(",", $chunk);
//			foreach($chunk as $member_id)
//			{
			// If the recipient is a member, load member from API
			$ch = new CurlBrowser;
			// TODO: Gateway from config
			$result = $ch->call("GET", "http://makeradmin-apigateway/membership/member?member_ids={$str_ids}&per_page={$chunkSize}");

			// Send an error message if the API request was unsuccessful
			if($ch->getStatusCode() != 200)
			{
				return Response()->json([
					"status" => "error",
					"message" => "An unexpected error occured while trying to load data from the membership module",
				], 502);
			}

			// Add the member to the recipient list
			foreach($ch->getJson()->data as $member)
			{
				$recipientList[$member->member_id] = $member;
			}
//			}
		}

		// Create new mail
		$message = new MessageModel;
		$message->message_type = $json["message_type"];
		$message->subject      = $json["message_type"] == "sms" ? $json["body"] : $json["subject"];
		$message->body         = $json["body"];
		$message->status       = "queued";

		// Validate input
		$message->validate();

		// Save entity
		$message->save();

		// Go through the recipient list and create queued messages in the database
		foreach($recipientList as $member)
		{
			$recipient = null;

			// Preprocess tokens
			$subject = $this->_proprocessTokens($json["subject"], $member);
			$body    = $this->_proprocessTokens($json["body"], $member);

			// Populate SMS / email
			if($json["message_type"] == "email")
			{
				$recipient = $member->email;
			}
			else if($json["message_type"] == "sms")
			{
				$recipient = $member->phone;

				// For SMS messages we want the subject to be equal to the content so the listing and sorting works in UI
				$subject = $body;
			}

			// Note: We queue messages even if $recipient is empty. We want still want them in the database, even if the backend are not able to send any message.

			// Create new recipient
			$entity = new RecipientModel;
			$entity->message_id = $message->entity_id;
			$entity->subject    = $subject;
			$entity->body       = $body;
			$entity->member_id  = $member->member_id;
			$entity->recipient  = $recipient;
			$entity->date_sent  = null;
			$entity->status     = "queued";

			// Validate input
			$entity->validate();

			// Save entity
			$entity->save();
		}

		// Send response to client
		return Response()->json([
			"status" => "created",
			"data" => $message->toArray(),
		], 201);
	}

	/**
	 * Load a queued/sent messages
	 */
	function read(Request $request, $message_id)
	{
		// Load the product
		$message = MessageModel::load([
			"message_id" => ["=", $message_id]
		]);

		// Generate an error if there is no such product
		if(false === $message)
		{
			return Response()->json([
				"message" => "No product with specified product id",
			], 404);
		}
		else
		{
			return Response()->json([
				"data" => $message->toArray(),
			], 200);
		}
	}

	/**
	 * TODO: Preprocess all tokens in the message
	 */
	function _proprocessTokens($input, $member)
	{
		$input = str_replace("##expirydate##",    "2016-12-31",       $input); // TODO
		$input = str_replace("##member_number##", $member->member_id, $input); // TODO: member_number
		$input = str_replace("##firstname##",     $member->firstname, $input);
		$input = str_replace("##lastname##",      $member->lastname,  $input);

		return $input;
	}
}