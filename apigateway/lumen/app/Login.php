<?php

namespace App;

use DB;
use Makeradmin\Exceptions\ServiceRequestTimeout;
use Makeradmin\Logger;
use Makeradmin\SecurityHelper;
use Makeradmin\Libraries\CurlBrowser;
use App\MakerGuard as Auth;

/**
 * TODO:
 *   Skall gå att köra en hårdkodad authenticate när membership-modulen inte är registrerad, annars kan den ej registrera sig själv
 *   check for expiry date
 */
class Login
{
	/** User ID of services */
	const SERVICE_USER_ID = -1;

	/**
	 * Authenticate the user with the Membership service
	 */
	public static function authenticate($username, $password)
	{
		// Get endpoint URL for membership module
		if(($service = Service::getService("membership")) === false)
		{
			// If no service is specified we should just throw an generic error saying the service could not be contacted
			throw new ServiceRequestTimeout;
		}

		// Send the request
		$ch = new CurlBrowser();
		$signed_permissions = SecurityHelper::signPermissionString('service', $service->signing_token);
		SecurityHelper::addPermissionHeaders($ch, Login::SERVICE_USER_ID, $signed_permissions);
		$result = $ch->call("POST", "{$service->endpoint}/membership/authenticate", [], [
			"username" => $username,
			"password" => $password,
		]);

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Return the user_id or false if unsuccessful
		if($ch->getStatusCode() == 200 && ($data = $ch->getJson()->data) !== false && isset($data->member_id))
		{
			return $data->member_id;
		}
		else
		{
			return false;
		}
	}

	/**
	 * Create a access token for a user and store it in database
	 */
	public static function createUserToken($user_id)
	{
		if ($user_id <= 0){
			throw new \Exception("user_id must be a positive number");
		}
		// Create a cryptographically safe access token
		$bearer = static::createAccessToken();

		// Insert into database
		$expires = (new \DateTime("now + 5 min", new \DateTimeZone("UTC")))->format('Y-m-d\TH:i:s');
		$tokens = DB::table("access_tokens")->insert([
			"user_id"      => $user_id,
			"access_token" => $bearer,
			"expires"      => $expires,
			"browser"      => $_SERVER["HTTP_USER_AGENT"] ?? null,
			"ip"           => $_SERVER["REMOTE_ADDR"],
			"lifetime"     => 1209600, // Lifetime 14 days = 60*60*24*14
		]);

		// Return result
		if($tokens)
		{
			return [
				"access_token" => $bearer,
				"expires"      => $expires,
			];
		}
		else
		{
			return false;
		}
	}

	/**
	 * Remove an access token from the database
	 */
	public static function removeToken($access_token)
	{
		// Remove access token from databas
		$num = DB::table("access_tokens")
			->where("access_token", $access_token)
			->where("user_id",      Auth::get()->user()->user_id)
			->delete();

		// One line should have been removed
		return $num == 1 ? true : false;
	}

	/**
	 * Return all tokens for a user
	 */
	public static function getUserTokens($user_id)
	{
		// TODO: Check expiry date
		return DB::Table("access_tokens")
			->select("access_token", "browser", "ip")
			->selectRaw("DATE_FORMAT(expires, '%Y-%m-%dT%H:%i:%sZ') AS expires")
			->where("user_id", $user_id)
			->get();
	}

	/**
	 * Generate an reset password token and send an E-mail
	 */
	public static function reset()
	{
		// TODO: Check that the E-mail is existing
		// TODO: Create a record in database with the reset token
		// TODO: Send an E-mail to the user
	}

	/**
	 * Read access token data from database
	 */
	public static function getAccessTokenData($access_token)
	{
		$result = DB::table("access_tokens")
			->where("access_token", $access_token)
			->select("user_id", "access_token", DB::raw("DATE_FORMAT(expires, '%Y-%m-%dT%H:%i:%sZ') as expires"),
			"browser", "permissions", "ip", "lifetime")
			->first();

		if ($result) {
			$now = new \DateTime();
			$expires = \DateTime::createFromFormat(\DateTime::ISO8601, $result->expires);
			if ($expires <= $now) {
				$result = null;
				DB::table("access_tokens")->where("access_token", $access_token)->delete();
			} else if (isset($result->user_id)) {
				$result->user_id *= 1; // Convert user_id to numeric;
			}
		} else {
		}
		return $result;
	}

	/**
	 * Update the access token
	 *
	 * Extend expiry date
	 * Update IP
	 * Update user agent
	 */
	public static function updateToken($access_token)
	{
		DB::table("access_tokens")
			->where("access_token", $access_token)
			->update(
				[
					"browser" => $_SERVER["HTTP_USER_AGENT"] ?? null,
					"ip"      => $_SERVER["REMOTE_ADDR"],
					"expires" => DB::raw("DATE_ADD(NOW(), INTERVAL CAST(lifetime AS UNSIGNED) SECOND)"),
				]
			);
	}

	/**
	 * Get the user object related to the user_id
	 */
	public static function getUserFromId($user_id){
		if ((!is_int($user_id)) || $user_id <= 0) {
			return null;
		}
		// Get endpoint URL for membership module
		if(($service = Service::getService("membership")) === false)
		{
			// If no service is specified we should just throw an generic error saying the service could not be contacted
			throw new ServiceRequestTimeout;
		}

		// Make a request to the membership module and load the user object (including groups and permissions)
		$ch = new CurlBrowser();
		$signed_permissions = SecurityHelper::signPermissionString('service', $service->signing_token);
		SecurityHelper::addPermissionHeaders($ch, Login::SERVICE_USER_ID, $signed_permissions);
		$result = $ch->call("GET", "{$service->endpoint}/membership/member/{$user_id}");

		if($ch->getStatusCode() == 200 && ($json = $ch->getJson()) !== false && isset($json->data->member_id))
		{
			$user = (object) $json->data;
			return $user;
		}
		return null;
	}

	/**
	 * Get the permissions assigned to a user
	 */
	public static function getUserPermissionsFromId($user_id){
		if ((!is_int($user_id)) || $user_id <= 0) {
			return null;
		}
		// Get endpoint URL for membership module
		if(($service = Service::getService("membership")) === false)
		{
			// If no service is specified we should just throw an generic error saying the service could not be contacted
			throw new ServiceRequestTimeout;
		}

		// Make a request to the membership module and load the user object (including groups and permissions)
		$ch = new CurlBrowser();
		$signed_permissions = SecurityHelper::signPermissionString('service', $service->signing_token);
		SecurityHelper::addPermissionHeaders($ch, Login::SERVICE_USER_ID, $signed_permissions);
		$result = $ch->call("GET", "{$service->endpoint}/membership/member/{$user_id}/permissions");

		if($ch->getStatusCode() == 200 && ($json = $ch->getJson()) !== false && isset($json->data)){
			return implode(',', array_column($json->data,'permission'));
		}
		return null;
	}

	public static function updateUserPermissions($user_id){
		$permissions = self::getUserPermissionsFromId($user_id);
		if (is_null($permissions)) {
			return false;
		}
		DB::table("access_tokens")
			->where('user_id', $user_id)
			->update(['permissions' => $permissions]);

		return $permissions;
	}

	public static function initializeAccessTokens() {
		// Remove any old access token for services
		DB::table("access_tokens")->where("user_id", Login::SERVICE_USER_ID)->delete();

		// Add access token for services
		$expires = (new \DateTime("now + 3650 day", new \DateTimeZone("UTC")))->format('Y-m-d\TH:i:s');
		DB::table("access_tokens")->insert([
			// The first user has an ID of 1, so this will not cause conflicts. Note however that an id of 0 would cause problems because the code uses checks on the form 'if($user_id)' all the time and 0 is converted to false in php.
			"user_id"      => Login::SERVICE_USER_ID,
			"access_token" => getenv('BEARER'),
			"expires"      => $expires,
			"browser"      => "",
			"permissions"  => 'service',
			"ip"           => "",
			"lifetime"     => 315360000, // Lifetime of approx 10 years = 60 * 60 * 24 * 365 * 10 s 
		]);
	}

	/**
	 * Get the user object related to the access_token
	 */
	public static function getUserIdFromAccessToken($access_token)
	{
		// Get the user_id related to the access token
		$access_token_data = self::getAccessTokenData($access_token);
		$user_id = isset($access_token_data->user_id) ? $access_token_data->user_id : false;

		if($user_id)
		{
			// Create a new user object and add user_id
			$user_permissions = $access_token_data->permissions;
			if (is_null($user_permissions)) {
				$user_permissions = self::updateUserPermissions($user_id);
			}
			if (is_string($user_permissions)) {
				$x = new \stdClass();
				$x->user_id = $user_id;
				$x->permissions = $user_permissions;
				return $x;
			}
		}
		return false;
	}

	/**
	 * Get the user object related to the access_token
	 */
	public static function getUserFromAccessToken($access_token)
	{
		// Get the user_id related to the access token
		$access_token_data = self::getAccessTokenData($access_token);
		$user_id = isset($access_token_data->user_id) ? $access_token_data->user_id : false;

		$user = self::getUserFromId($user_id);
		if ($user !== null) {
			$user->user_id = $user->member_id;
		}
		return $user;
	}

	/**
	 * Log a successful login
	 */
	public static function logSuccess($user_id)
	{
		// Write log
		DB::table("login")->insert([
			"success" => 1,
			"user_id" => $user_id,
			"ip" => $_SERVER["REMOTE_ADDR"],
		]);
	}

	/**
	 * Log a failed login attempt
	 */
	public static function logFail()
	{
		// Write log
		DB::table("login")->insert([
			"success" => 0,
			"user_id" => null,
			"ip" => $_SERVER["REMOTE_ADDR"],
		]);
	}

	/**
	 * Figure out if the login should be throttled or not
	 *
	 * TODO: Values should be configured in a config
	 */
	public static function shouldThrottle()
	{
		// Get the number of failed attempts the last hour
		$x = DB::table("login")
			->where("ip", $_SERVER["REMOTE_ADDR"])
			->where("success", 0)
			->whereRaw("date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
			->count();

		// If we have more than 10 failed attempts we should throttle
		return ($x > 10);
	}

	/**
	 * Create a cryptographically safe base 62 encoded access token
	 */
	public static function createAccessToken()
	{
		$chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
		$result = "";
		for($i = 0; $i < 32; $i++)
		{
			$x = ord(random_bytes(1)) % strlen($chars);
			$result .= $chars[$x];
		}
		return $result;
	}
}
