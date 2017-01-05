<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Libraries\CurlBrowser;

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
	public function fire()
	{
		$this->info("Unregister service");

		// Send the request to API Gateway
		$ch = new CurlBrowser();
		$ch->useJson();
		$result = $ch->call("POST", "http://" . config("service.gateway") . "/service/unregister", [], [
			"url"     => config("service.url"),
			"version" => config("service.version"),
		]);

		print_r($ch->getJson());
	}
}