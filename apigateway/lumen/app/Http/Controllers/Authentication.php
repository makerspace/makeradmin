<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

use App\Login;
use App\Exceptions\EntityValidationException;
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
		$username   = $request->get("username");
		$password   = $request->get("password");
		$grant_type = $request->get("grant_type");

		// Too many failed attempts?
		if(Login::shouldThrottle())
		{
			return Response()->json([
				"status"  => "error",
				"message" => "Your have reached your maximum number of failed login attempts for the last hour. Please try again later.",
			], 429);
		}

		// Validate input
		if($grant_type != "password")
		{
			throw new EntityValidationException("grant_type", null, "Unknown grant type");
		}
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

		// Create a token and store in database
		$token = Login::createToken($user_id);
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
		$user_id = Auth::user()->user_id;

		// Get users access tokens from the database
		$result = Login::getTokens($user_id);

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