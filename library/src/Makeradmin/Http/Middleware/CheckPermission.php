<?php

namespace Makeradmin\Http\Middleware;

use Closure;
use \Illuminate\Http\Request;
use Makeradmin\SecurityHelper;

class CheckPermission
{
	const DEFAULT_REQUIRED_PERMISSION = SecurityHelper::DEFAULT_REQUIRED_PERMISSION;
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
		//TODO: add signing token string from config
		$user_permissions = SecurityHelper::verifyPermissionString($request->header("X-User-Permissions"), ''/*config(service.signing_token')*/);

		if ($user_permissions !== false &&
			SecurityHelper::checkPermission($required_permission, $user_permissions) === true) 
		{
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