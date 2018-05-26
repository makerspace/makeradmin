<?php
namespace App\Console\Commands;
use Illuminate\Console\Command;
use App\Login;
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
	public function fire()
	{
		Login::initializeAccessTokens();
	}
}
