<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use App\Exceptions\EntityValidationException;
use App\Service;
use App\Logger;
use App\Login;
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

		// TODO: Better validation
		if(empty($json["name"]))
		{
			throw new EntityValidationException("name", "required");
		}
		if(empty($json["url"]))
		{
			throw new EntityValidationException("url", "required");
		}
		if(empty($json["endpoint"]))
		{
			throw new EntityValidationException("endpoint", "required");
		}
		if(empty($json["version"]))
		{
			throw new EntityValidationException("version", "required");
		}

		// TODO: Check permissions

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

		// TODO: Better validation
		if(empty($json["url"]))
		{
			throw new EntityValidationException("url", "required");
		}
		if(empty($json["version"]))
		{
			throw new EntityValidationException("version", "required");
		}

		// TODO: Check permissions

		// Unregister the service
		Service::unregister([
			"url"     => $json["url"],
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

		// Check permissions
		$user = Auth::user();
//		print_r($user);
		// TODO: Send an API request to get the roles and permissions of the user

		// Get a list of all groups where the user have a "api exec" permission
		$groups = [];
		foreach($user->roles as $role)
		{
			foreach($role->permissions as $permission)
			{
				if($permission->permission == "api exec")
				{
					$groups[] = $permission->group_id;
				}
			}
		}
		print_r($groups);
		die("roles\n");



		// List services
		$result = Service::all();

		// Send response to client
		return Response()->json([
			"data"  => $result,
		], 200);
	}

	/**
	 * Handle an incoming HTTP request
	 *
	 * Finds the appropriate micro service and sends a HTTP request to it
	 */
	public function handleRoute(Request $request, $p1, $p2 = null, $p3 = null, $p4 = null, $p5 = null)
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
			$ch->setHeader("X-User-Id", $user->user_id);
		}

		// Get JSON and POST data
		$e = explode(";", $request->header("Content-Type"));
		$type = is_array($e) ? $e[0] : $request->header("Content-Type");
		if($type == "application/json")
		{
			$post = $request->json()->all();
			$ch->useJson();
		}
		else if($type == "multipart/form-data")
		{
			// Change data from the the ISO-8859-1 HTTP to UTF-8
			// TODO: Is this one affected by the encoding headers in HTTP and/or settings in server?
			$post = utf8_encode($request->getContent());

			// Forward the content-type
			$ch->setHeader("Content-Type", $request->header("Content-Type"));
		}
		else
		{
			$post = [];
		}

		// Create a new url with the service endpoint url included
		$url = $service->endpoint . implode("/", $path);

		// Send the request
		// Forward the query string parameters like ?sort_by=column etc to the internal request
		$result = $ch->call($request->method(), $url, $request->query->all(), $post);
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