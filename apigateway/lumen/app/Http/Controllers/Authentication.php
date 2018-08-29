<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use App\MakerGuard as Auth;

use App\Login;
use Makeradmin\Exceptions\EntityValidationException;
use DB;

/**
 * Controller for authentication stuff
 */
class Authentication extends Controller
{
	/**
	 * Login and create an access token in the database if login was successful
	 */
	public function login(Request $request)
	{
		$grant_type = $request->get("grant_type");

		// Too many failed attempts?
		if(Login::shouldThrottle())
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Your have reached your maximum number of failed login attempts for the last hour. Please try again later.",
			], 429);
		}

		if($grant_type == "password")
		{
			// Use password validation
			// Validate input
			$username   = $request->get("username");
			$password   = $request->get("password");
			
			if(empty($username))
			{
				throw new EntityValidationException("username", "required");
			}
			

			if(empty($password))
			{
				throw new EntityValidationException("password", "required");
			}

			// Send a request to membership module
			$user_id = Login::authenticate($username, $password);
			if(!$user_id)
			{
				Login::logFail($user_id);
				return Response()->json([
					"status"  => "error",
					"message" => "The username and/or password you specified was incorrect",
				], 401);
			}
		}
		else
		{
			throw new EntityValidationException("grant_type", null, "Unknown grant type");
		}

		// Create a token and store in database
		$token = Login::createUserToken($user_id);
		Login::logSuccess($user_id);

		// Send response
		return Response()->json([
			"access_token" => $token["access_token"],
			"expires"      => $token["expires"],
		], 200);
	}

	/**
	 * Login and create an access token in the database if login was successful
	 */
	public function unauthenticated_login(Request $request)
	{
		$user_id = $request->get("user_id");
		if(empty($user_id))
		{
			throw new EntityValidationException("user_id", "required");
		}

		// Create a token and store in database
		$token = Login::createUserToken($user_id);
		Login::logSuccess($user_id);

		// Send response
		return Response()->json([
			"access_token" => $token["access_token"],
			"expires"      => $token["expires"],
		], 200);
	}

	/**
	 * Remove an access token from the database
	 */
	public function logout(Request $request, $access_token)
	{
		// Remove access token from databas
		if(Login::removeToken($access_token))
		{
			return Response()->json([
				"status"  => "ok",
				"message" => "The access_token have been successfully removed",
				"token"   => $access_token,
			], 200);
		}
		else
		{
			// Send error response
			return Response()->json([
				"status"  => "error",
				"message" => "The access_token you specified could not be found in the database",
				"token"   => $access_token,
			], 404);
		}
	}

	/**
	 * Return a list of all access tokens associated to the user
	 */
	public function listTokens(Request $request)
	{
		// Get user id
		$user_id = Auth::get()->user()->user_id;

		// Get users access tokens from the database
		$result = Login::getUserTokens($user_id);

		// Send response
		return Response()->json([
			"status" => "ok",
			"data"   => $result,
		], 200);
	}

	/**
	 * Request a new password
	 */
	public function reset(Request $request)
	{
		// TODO: Validate input

		// Generate a reset password token and send an E-mail
		Login::reset();

		// Send response
		return Response()->json([
			"status"  => "ok",
			"message" => "TODO: Reset password",
		], 200);
	}
}