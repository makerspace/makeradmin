<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Libraries\CurlBrowser;

use DB;

class Send extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "service:send";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Send all queued messages to the mail service provider";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function fire()
	{
		$this->info("Register service");

		// Get all messages from database
		$messages = DB::table("messages_recipient")
			->leftJoin("messages_message", "messages_message.messages_message_id", "=", "messages_recipient.messages_message_id")
			->selectRaw("messages_recipient.title AS subject")
			->selectRaw("messages_recipient.description AS body")
			->selectRaw("messages_message.message_type")
			->selectRaw("messages_recipient.recipient")
			->where("messages_recipient.status", "=", "queued")
			->limit(10)
			->get();

		// Create an clean array with data
		$list = [];
		foreach($messages as $message)
		{
			$list[] = $message;
		}

		// TODO: Send the request to to the gateway
		print_r($list);
/*
		$ch = new CurlBrowser();
		$ch->useJson();
		$result = $ch->call("POST", "http://" . config("service.gateway") . "/service/register", [
			"name"     => config("service.name"),
			"url"      => config("service.url"),
			"endpoint" => "http://" . gethostbyname(gethostname()) . ":80/",
			"version"  => config("service.version"),
		]);

		print_r($ch->getJson());
*/
	}
}