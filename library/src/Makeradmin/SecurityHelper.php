<?php
namespace Makeradmin;

use Laravel\Lumen\Application;
use Makeradmin\Libraries\CurlBrowser;

/**
 * Help functions to manage route permissions.
 */
class SecurityHelper {
	const PERMISSION_PREFIX = 'permission';
	const PREFIX_LENGTH = 10;
	const DEFAULT_REQUIRED_PERMISSION = 'service';

	public static function checkRoutePermissions(Application $app) {

		$used_permissions = [];
		$succeeded = true;
		$info = [];
		$routes = $app->router->getRoutes();
		foreach ($routes as $uri => $object) {
			$action = $object['action'];
			if (array_key_exists('middleware', $action) && !empty($middlwares = $action['middleware'])) {
				$permission_count = 0;
				foreach ($middlwares as $middleware_str) {
					if (strncmp($middleware_str, self::PERMISSION_PREFIX, self::PREFIX_LENGTH) === 0) {
						$permission_count++;
						$required_permission = substr($middleware_str, self::PREFIX_LENGTH + 1);
						$used_permissions[] = $required_permission;
						$info[] = "{$uri} requires permission: {$required_permission}";
					}
				}
				if ($permission_count == 0) {
					$succeeded = false;
					$info[] = "Error {$uri} does not require any permission";
				}
			} else {
				$succeeded = false;
				$info[] = "Error {$uri} does not require any permission";
			}
		}
		$result = [
			'succeeded' => $succeeded,
			'info' => $info,
			'permissions' => array_unique($used_permissions, SORT_STRING),
		];
		return $result;
	}

	/**
	 * Check if the user_permissions contains the required permission.
	 */
	public static function checkPermission($required_permission, $user_permissions) {
		$permissions = explode(",", $user_permissions);
		if (empty($required_permission)) {
			$required_permission = DEFAULT_REQUIRED_PERMISSION;
		}
		$has_permission =
			in_array('service', $permissions) || // Services can access anything
			in_array($required_permission, $permissions) ||
			$required_permission === 'public';
		return $has_permission;
	}

	/**
	 * Add user_id and permissions headers to CurlBrowser
	 */
	public static function addPermissionHeaders(CurlBrowser $ch, $user_id, $signed_user_permissions = '') {
		$ch->setHeader("X-User-Id", $user_id);
		$ch->setHeader("X-User-Permissions", $signed_user_permissions);
	}

	/**
	 * Add unauthorized user headers
	 */
	public static function addPermissionHeadersUnauthorized(CurlBrowser $ch) {
		$ch->setHeader("X-User-Id", 0);
		$ch->setHeader("X-User-Permissions", '');
	}

	public static function signPermissionString($permissions, $signing_token){
		// XXX: Implement sign permissions.
		return $permissions;
	}

	public static function verifyPermissionString($permissions, $signing_token){
		// XXX: Implement verify permissions.
		return $permissions;
	}

	public static function verifyPassword($password){
		// XXX: Enforce rules for passwords.
		return strlen($password) >= 6;
	}
}