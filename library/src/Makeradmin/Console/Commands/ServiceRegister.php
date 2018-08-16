<?php

namespace Makeradmin\Console\Commands;

use Illuminate\Console\Command;
use Makeradmin\Libraries\CurlBrowser;
use Makeradmin\SecurityHelper;

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
	public function handle()
	{
		$this->info("Registering service...");

		$permissions = SecurityHelper::checkRoutePermissions($this->getLaravel());

		if ($permissions['succeeded'] == false) {
			$this->info("Error: Some routes are missing permission definition");
			$this->info("       Use RoutePermissionGuard to insert default permission");
			$permission_json = json_encode($permissions,JSON_PRETTY_PRINT);
			$this->info("$permission_json");
			// TODO: Uncomment return when services supports permissions 
			// return;
		}

		// Send the request to API Gateway
		$ch = new CurlBrowser();
		$ch->useJson();
		$ch->setHeader("Authorization", "Bearer " . config("service.bearer"));
		$ch->call("POST", "http://" . config("service.gateway") . "/service/register", [], [
			"name"     => config("service.name"),
			"url"      => config("service.url"),
			"endpoint" => "http://" . gethostbyname(gethostname()) . ":80/",
			"version"  => config("service.version"),
		]);
		$result = $ch->getJson();
		if ($result->message == "The service was successfully registered") {
			print("Service registered\n");
		} else {
			print_r($result);
		}

		$ch->call("POST", "http://" . config("service.gateway") . "/membership/permission/register", [], [
			'service'     => config('service.name'),
			'permissions' => implode(',', $permissions['permissions']),
		]);
	}
}
