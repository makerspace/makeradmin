<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use App\Service;
use App\Logger;
use App\Libraries\CurlBrowser;

/**
 * Controller for the service registry
 */
class ServiceRegistry extends Controller
{
	/**
	 * Reqister a new micro service
	 */
	public function register(Request $request)
	{
		$json = $request->json()->all();

		// TODO: Check permissions
		// TODO: Better validation

		// Check that the service does not already exist
		if(Service::getService($json["url"], $json["version"]))
		{
			return Response()->json([
				"status"  => "error",
				"message" => "A service does alredy exist with identical URL and version",
			]);
		}

		// Register the service
		Service::register([
			"name"     => $json["name"],
			"url"      => $json["url"],
			"endpoint" => $json["endpoint"],
			"version"  => $json["version"],
		]);

		// Send response
		return Response()->json([
			"status"  => "registered",
			"message" => "The service was successfully registered",
		], 200);
	}

	/**
	 * Remove an existing micro service
	 */
	public function unregister(Request $request)
	{
		$json = $request->json()->all();

		// TODO: Check permissions
		// TODO: Better validation

		// Unregister the service
		Service::unregister([
			"name"    => $json["name"],
			"version" => $json["version"],
		]);

		// Send response
		return Response()->json([
			"status"  => "unregistered",
			"message" => "The service was successfully unregistered",
			"data"    => $json,
		], 200);
	}

	/**
	 * Return a list of all registered micro services
	 */
	public function list(Request $request)
	{
		$json = $request->json()->all();

		// TODO: Check permissions

		// List services
		$result = Service::all();

		return Response()->json([
			"data"  => $result,
		], 200);
	}

	/**
	 * Handle an incoming HTTP request
	 *
	 * Finds the appropriate micro service and sends a HTTP request to it
	 */
	public function handleRoute(Request $request, $p1, $p2 = null, $p3 = null, $p4 = null)
	{
		// Split the path into segments and get version + service
		$path = explode("/", $request->path());
		$service = $path[0];
		$version = 1;// TODO: Get version from header


		// Get the endpoint URL or throw an exception if no service was found
		if(($service = Service::getService($service, $version)) === false)
		{
			throw new NotFoundHttpException;
		}

		// Initialize cURL
		$ch = new CurlBrowser;

		// Add a header with authentication information
		$user = Auth::user();
		if($user)
		{
			$ch->setHeader("X-Member-Id", $user->user_id);
		}

		// Append the query string parameters like ?sort_by=column etc to the URL
		// TODO: $request->all() is not correct
		$ch->setQueryString($request->all());

		// Get JSON and POST data
		// TODO: Should not include query string parameters
		$data = json_encode($request->all());

		// Create a new url with the service endpoint url included
		$url = $service->endpoint . "/" . implode("/", $path);

		// Send the request
		$result = $ch->call($request->method(), $url, $data);
		$http_code = $ch->getStatusCode();

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Send response to client
		return response($result, $http_code)
			->header("Content-Type", "application/json");
	}

	/**
	 * Handles CORS requests
	 *
	 * This is an API, so everything should be allowed
	 */
	public function handleOptions(Request $request)
	{
		return response("", 200);
	}

	public function test()
	{
		$user = Auth::user();
		if(!$user)
		{
			return Response()->json([
				"status"  => "ok",
				"message" => "Hello not logged in user!",
			], 200);
		}
		else
		{
			return Response()->json([
				"status"  => "ok",
				"message" => "Hello user {$user->user_id}!",
			], 200);
		}
	}
}