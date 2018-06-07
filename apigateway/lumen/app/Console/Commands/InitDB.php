<?php
namespace App\Console\Commands;
use Illuminate\Console\Command;
use App\Login;
use DB;

class InitDB extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "db:init";
	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Initialize the database";
	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function handle() {
		// Delete all existing entries in the services table to clean up any old data from previous runs
		// (obviously no services are currently registered as the api-gateway just started)
		DB::table("services")->delete();
		Login::initializeAccessTokens();
	}
}
