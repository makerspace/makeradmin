<?php

namespace App;

use DB;
use App\Exceptions\ServiceRequestTimeout;
use App\Logger;
use App\Libraries\CurlBrowser;
use Illuminate\Support\Facades\Auth;

/**
 * TODO:
 *   Skall gå att köra en hårdkodad authenticate när membership-modulen inte är registrerad, annars kan den ej registrera sig själv
 *   check for expiry date
 */
class Login
{
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
		$url = "{$service->endpoint}/membership/authenticate";

		// Send the request
		$ch = new CurlBrowser();
		$result = $ch->call("POST", "{$service->endpoint}/membership/authenticate", [
			"username" => $username,
			"password" => $password,
		]);

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Return the user_id or false if unsuccessful
		if($ch->getStatusCode() == 200 && ($data = $ch->getJson()) !== false && isset($data->member_id))
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
	public static function createToken($user_id)
	{
		// Create a cryptographically safe access token
		$bearer = static::createAccessToken();

		// Insert into database
		$expires = date("Y-m-d\TH:i:s\Z", strtotime("now + 30 day"));
		$tokens = DB::table("access_tokens")->insert([
			"user_id"      => $user_id,
			"access_token" => $bearer,
			"expires"      => $expires,
			"browser"      => $_SERVER["HTTP_USER_AGENT"],
			"ip"           => $_SERVER["REMOTE_ADDR"],
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
			->where("user_id",      Auth::user()->member_id)
			->delete();

		// One line should have been removed
		return $num == 1 ? true : false;
	}

	/**
	 * Return all tokens for a user
	 */
	public static function getTokens($user_id)
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
					"browser" => $_SERVER["HTTP_USER_AGENT"],
					"ip"      => $_SERVER["REMOTE_ADDR"],
					"expires" => DB::raw("CURRENT_TIME"),
				]
			);
	}

	/**
	 * Get the user object related to the access_token
	 */
	public static function getUserFromAccessToken($access_token)
	{
		// Get the user_id related to the access token
		$user_id = DB::table("access_tokens")
			->where("access_token", $access_token)
			->value("user_id");

		// Get endpoint URL for membership module
		if(($service = Service::getService("membership")) === false)
		{
			return false;
		}
		$url = "{$service->endpoint}/membership/authenticate";
		// Make a request to the membership module and load the user object (including roles and permissions)
		$ch = new CurlBrowser();
		$result = $ch->call("GET", "{$service->endpoint}/membership/member/{$user_id}", []);

		if($ch->getStatusCode() == 200 && ($json = $ch->getJson()) !== false && isset($json->data->member_id))
		{
			$x = new \stdClass();
			$x->user_id = $json->data->member_id;
			return $x;
		}
		else
		{
			return false;
		}
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