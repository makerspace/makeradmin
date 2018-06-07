<?php

namespace App;

use Closure;
use Illuminate\Contracts\Auth\Authenticatable;
use Makeradmin\Logger;
use Makeradmin\SecurityHelper;
use Makeradmin\Exceptions\ServiceRequestTimeout;
use Makeradmin\Libraries\CurlBrowser;
use DB;

class MakerGuard
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

	/** Determine if the requester is external service */
	public function is_external_service()
	{
		if(!$this->user)
		{
			return false;
		}
		return $this->user->user_id < Login::SERVICE_USER_ID;
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

	public function setUserObject($user)
	{
		$this->user = $user;
	}

	public function handle($request, Closure $next, $guard = null)
	{
		return $next($request);
	}

	public static function get()
	{
		// Returns the singleton instance from AuthServiceProvider
		return app()->make('App\MakerGuard');
	}
}