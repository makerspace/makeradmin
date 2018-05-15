<?php

namespace Makeradmin\Http\Middleware;

use Closure;
use \Illuminate\Http\Request;

class CheckPermission
{
	const DEFAULT_REQUIRED_PERMISSION = 'service';
	/**
	 * Create a new middleware instance.
	 *
	 * @return void
	 */
	public function __construct() {
	}

	/**
	 * Handle an incoming request.
	 *
	 * @param  \Illuminate\Http\Request  $request
	 * @param  \Closure  $next
	 * @param  string|null  $group
	 * @return mixed
	 */
	public function handle(Request $request, Closure $next, $required_permission = DEFAULT_REQUIRED_PERMISSION) {
		$permissions = explode(",", $request->header("X-User-Permissions"));
		if (empty($required_permission)) {
			$required_permission = DEFAULT_REQUIRED_PERMISSION;
		}
		$has_permission = array_search($required_permission, $permissions);

		if ($has_permission === false) {
			return Response()->json([
				"status" => "error",
				"message" => "Unauthorized",
			], 401);
		}

		$response = $next($request);
		return $response;
	}
}