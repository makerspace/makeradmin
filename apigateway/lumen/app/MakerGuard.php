<?php

namespace App;

use Closure;
use Illuminate\Contracts\Auth\Authenticatable;
use \Illuminate\Contracts\Auth\Guard;
use DB;

class MakerGuard implements Guard
{
	protected $user;

	/**
	 * Determine if the current user is authenticated.
	 *
	 * @return bool
	 */
	public function check()
	{
		if(!$this->user)
		{
			return false;
		}

		return $this->user->user_id;
	}

	/**
	 * Determine if the current user is a guest.
	 *
	 * @return bool
	 */
	public function guest()
	{
		return !$this->check();
	}

	/**
	 * Get the currently authenticated user.
	 *
	 * @return \Illuminate\Contracts\Auth\Authenticatable|null
	 */
	public function user()
	{
		if(!$this->user)
		{
			return false;
		}

		return $this->user;
	}

	/**
	 * Get the ID for the currently authenticated user.
	 *
	 * @return int|null
	 */
	public function id()
	{
		die("\nNot implemented: id()\n");
	}

	/**
	 * Validate a user's credentials.
	 *
	 * @param  array  $credentials
	 * @return bool
	 */
	public function validate(array $credentials = [])
	{
		die("\nNot implemented: validate()\n");
	}

	/**
	 * Set the current user.
	 *
	 * @param  \Illuminate\Contracts\Auth\Authenticatable  $user
	 * @return void
	 */
	public function setUser(Authenticatable $user)
	{
		die("\nNot implemented: setUser()\n");
	}

	public function setUserObject($user)
	{
		$this->user = $user;
	}

	public function setUserId($user_id)
	{
		die("setUserId\n");
	}

	public function handle($request, Closure $next, $guard = null)
	{
		return $next($request);
	}
}