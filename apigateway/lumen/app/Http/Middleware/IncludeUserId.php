<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Contracts\Auth\Factory as Auth;
use App\Login;

class IncludeUserId
{
	/**
	 * The authentication guard factory instance.
	 *
	 * @var \Illuminate\Contracts\Auth\Factory
	 */
	protected $auth;

	/**
	 * Create a new middleware instance.
	 *
	 * @param  \Illuminate\Contracts\Auth\Factory  $auth
	 * @return void
	 */
	public function __construct(Auth $auth)
	{
		$this->auth = $auth;
	}

	/**
	 * Handle an incoming request.
	 *
	 * @param  \Illuminate\Http\Request  $request
	 * @param  \Closure  $next
	 * @param  string|null  $guard
	 * @return mixed
	 */
	public function handle($request, Closure $next, $guard = null)
	{
		// Get the access token from header
		$header = $request->header("Authorization");
		$access_token = trim(preg_replace('/^(?:\s+)?Bearer\s/', '', $header));

		// Find the access token in the database and set user_id if found
		if(($user = Login::getUserFromIdAccessToken($access_token)) !== false)
		{
			Login::updateToken($access_token);
			$this->auth->guard($guard)->setUserObject($user);
		}

		return $next($request);
	}
}