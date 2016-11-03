<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Contracts\Auth\Factory as Auth;
use DB;

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

		// Find the access token in the database
		$user = DB::table("access_tokens")
			->select("user_id")
			->where("access_token", $access_token)
			->first();

		// Save the user_id
		if($user)
		{
			$this->auth->guard($guard)->setUserId($user->user_id);
		}

		return $next($request);
	}
}