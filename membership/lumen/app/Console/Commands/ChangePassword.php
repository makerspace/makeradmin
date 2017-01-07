<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Member as MemberModel;

class ChangePassword extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "member:password {username} {password}";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Change password for a member";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function fire()
	{
		$this->info("Changing password");

		// Create new member
		$entity = MemberModel::load([
			"email" => $this->argument("username"),
		]);

		if($entity === false)
		{
			$this->error("Could not find member in database");
			return;
		}

		// Calculate a new password hash
		$entity->password  = password_hash($this->argument("password"), PASSWORD_DEFAULT);

		// Save the entity
		$entity->save();

		$this->info("OK");
	}
}