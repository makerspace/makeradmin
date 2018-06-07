<?php

namespace App\Http\Middleware;

use Closure;
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
	 * @param  string|null  $group
	 * @return mixed
	 */
	public function handle($request, Closure $next, $group = null)
	{
		$guard = $this->auth;

		if ($group === "public") $valid = True;
		else if ($group === "service") $valid = $guard->is_service();
		else if ($group === null) $valid = $guard->check(); // Check if a user (or a service) is logged in
		else die("Unknown group '" . $group . "'");

		if (!$valid) {
			return Response()->json([
				"status" => "error",
				"message" => "Unauthorized",
			], 401);
		}

		return $next($request);
	}
}