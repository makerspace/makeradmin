<?php

namespace Makeradmin\Console\Commands;

use Illuminate\Console\Command;
use \Makeradmin\Libraries\CurlBrowser;

class ServiceUnregister extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "service:unregister";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Unregister this service to the API gateway";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function handle()
	{
		// Send the request to API Gateway
		$ch = new CurlBrowser();
		$ch->useJson();
		$ch->setHeader("Authorization", "Bearer " . config("service.bearer"));
		$ch->call("POST", "http://" . config("service.gateway") . "/service/unregister", [], [
			"url"     => config("service.url"),
			"version" => config("service.version"),
		]);
		$result = $ch->getJson();

		if ($result->message == "The service was successfully unregistered") {
			print("Service unregistered\n");
		} else {
			print_r($result);
		}
	}
}
