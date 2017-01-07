<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Libraries\CurlBrowser;

class ServiceRegister extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "service:register";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Register this service to the API gateway";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function fire()
	{
		$this->info("Register service");

		// Send the request to API Gateway
		$ch = new CurlBrowser();
		$ch->useJson();
		$ch->setHeader("Authorization", "Bearer " . config("service.bearer"));
		$result = $ch->call("POST", "http://" . config("service.gateway") . "/service/register", [], [
			"name"     => config("service.name"),
			"url"      => config("service.url"),
			"endpoint" => "http://" . gethostbyname(gethostname()) . ":80/",
			"version"  => config("service.version"),
		]);

		print_r($ch->getJson());
	}
}