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
	 * @param  string|null  $required_permission
	 * @return mixed
	 */
	public function handle(Request $request, Closure $next, $required_permission = DEFAULT_REQUIRED_PERMISSION) {
		$user_permissions_string = $request->header("X-User-Permissions");
		//TODO: validate $user_permissions_string
		$permissions = explode(",", $user_permissions_string);
		if (empty($required_permission)) {
			$required_permission = DEFAULT_REQUIRED_PERMISSION;
		}
		$has_permission = 
			in_array('service', $permissions) || // Services can access anything
			in_array($required_permission, $permissions) ||
			$required_permission === 'public';

		if ($has_permission === true) {
			$response = $next($request);
			return $response;
		} else {
			return Response()->json([
				"status" => "error",
				"message" => "Unauthorized",
			], 401);
		}
	}
}