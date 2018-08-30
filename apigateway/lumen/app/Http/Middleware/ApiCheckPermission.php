<?php

namespace App\Http\Middleware;

use Closure;
use \Illuminate\Http\Request;
use Makeradmin\SecurityHelper;
use App\MakerGuard;

class ApiCheckPermission
{
	const DEFAULT_REQUIRED_PERMISSION = SecurityHelper::DEFAULT_REQUIRED_PERMISSION;

	
	protected $auth;
	/**
	 * Create a new middleware instance.
	 *
	 * @return void
	 */
	public function __construct(MakerGuard $auth) {
		$this->auth = $auth;
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
		$user_permissions = $this->auth->user()->permissions ?? "";
		$has_permission = SecurityHelper::checkPermission($required_permission, $user_permissions);

		if ($has_permission === true) {
			$response = $next($request);
			return $response;
		} else {
			return Response()->json([
				"status" => "error",
				"message" => "Forbidden",
			], 403);
		}
	}
}