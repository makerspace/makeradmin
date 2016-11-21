<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Member as MemberModel;

class CreateUser extends Command
{

	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "member:create {username} {password}";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Create a new member";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function fire()
	{
		$this->info("Creating new member");

		// Create new member
		$entity = new MemberModel;
		$entity->email     = $this->argument("username");
		$entity->password  = password_hash($this->argument("password"), PASSWORD_DEFAULT);
		$entity->firstname = $this->argument("username");

		// Validate input
		$entity->validate();

		// Save the entity
		$entity->save();

		$this->info("OK");
	}
}