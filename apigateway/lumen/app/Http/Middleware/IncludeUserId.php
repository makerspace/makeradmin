<?php

namespace App\Http\Middleware;

use Closure;
use App\MakerGuard;
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
	 * @return void
	 */
	public function __construct(MakerGuard $auth)
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
		if(($user = Login::getUserIdFromAccessToken($access_token)) !== false)
		{
			Login::updateToken($access_token);
			$this->auth->setUserObject($user);
		}

		return $next($request);
	}
}