<?php

namespace App;

use Closure;
use Illuminate\Contracts\Auth\Authenticatable;
use \Illuminate\Contracts\Auth\Guard;
use App\Exceptions\ServiceRequestTimeout;
use App\Libraries\CurlBrowser;
use App\Login;
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

	/** Determine if the requester is another service */
	public function is_service()
	{
		if(!$this->user)
		{
			return false;
		}
		return $this->user->user_id == Login::SERVICE_USER_ID;
	}

	/** Determine if the user is in the specified group */
	public function check_group($group)
	{
		if ($group === null) die("No group specified for this route.");

		// Check if there is any user logged in at all
		if (!$this->check()) return false;

		// The special service group only contains services.
		// Used to ensure some routes can only be reached by the internal network
		if ($group === "service") {
			return $this->is_service();
		}

		// Get endpoint URL for membership module
		if(($service = Service::getService("membership")) === false) {
			// If no service is specified we should just throw an generic error saying the service could not be contacted
			throw new ServiceRequestTimeout;
		}

		// Send the request
		$ch = new CurlBrowser();
		$result = $ch->call("GET", "{$service->endpoint}/membership/member/" . $this->user->user_id . "/groups");

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Return the user_id or false if unsuccessful
		if($ch->getStatusCode() == 200 && ($data = $ch->getJson()->data) !== false) {
			foreach ($data as $user_group) {
				if ($user_group->name === $group) {
					return true;
				}
			}
		}

		return false;
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