<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Contracts\Auth\Factory as Auth;
use App\MakerGuard;

class Authenticate
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
	 * @param  string|null  $group
	 * @return mixed
	 */
	public function handle($request, Closure $next, $group = null)
	{
		// I'm tired of this overengineering
		$guard = $this->auth->guard(null);
		// Services are assumed to have full access to everything.
		// If the user is not a service then check if it is in the specified group (or just logged in if no group was specified)
		if (!$guard->is_service() && ($group === null ? !$guard->check() : !$guard->check_group($group))) {
			return Response()->json([
				"status" => "error",
				"message" => "Unauthorized",
			], 401);
		}

		return $next($request);
	}
}