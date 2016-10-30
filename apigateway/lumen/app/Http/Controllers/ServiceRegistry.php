<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

class ServiceRegistry extends Controller
{
	public function register(Request $request)
	{
		$json = $request->json()->all();

		// TODO: Register service

		return Response()->json([
			"status"  => "registered",
			"message" => "The service was successfully registered",
			"data"    => $json,
		], 200);
	}

	public function unregister(Request $request)
	{
		$json = $request->json()->all();

		// TODO: Unregister service

		return Response()->json([
			"status"  => "unregistered",
			"message" => "The service was successfully unregistered",
			"data"    => $json,
		], 200);
	}

	public function list(Request $request)
	{
		$json = $request->json()->all();

		// TODO: List services

		return Response()->json([
			"data"  => [],
		], 200);
	}

	public function handleRoute(Request $request, $p1, $p2 = null, $p3 = null, $p4 = null)
	{
		// Split the path into segments and get version + service
		$path = explode("/", $request->path());
		$version = $path[0];
		$service = $path[1];

		// TODO: Should be in database
		$services = [
			"membership" => [
				"name"     => "Membership Micro Service",
				"url"      => "/membership",
				"endpoint" => "http://172.19.0.4:80",
				"version"  => "1.0",
			],
			"economy" => [
				"name"     => "Economy Micro Service",
				"url"      => "/economy",
				"endpoint" => "http://172.19.0.5:80",
				"version"  => "1.0",
			],
		];
		if(array_key_exists($service, $services))
		{
			$endpoint = $services[$p1]["endpoint"];
		}
		else
		{
			throw new NotFoundHttpException;
		}

		// Combine into a new path without the version prefix
		array_shift($path);
		$p = implode("/", $path);
		$url = "{$endpoint}/{$p}";

		// Initialize cURL
		$ch = curl_init();
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
		curl_setopt($ch, CURLOPT_HEADER, false);

		// Add a header with authentication information
		$user = Auth::user();
		if($user)
		{
			curl_setopt($ch, CURLOPT_HTTPHEADER,
				[
					"X-Member-Id: {$user->user_id}",
				]
			);
		}

		// Append the query string parameters like ?sort_by=column etc to the URL
		$querystring = http_build_query($request->all(), "", "&");
		if(!empty($querystring))
		{
			$url .= "?{$querystring}";
		}

		// Set the URL
		curl_setopt($ch, CURLOPT_URL, $url);

		// Use the correct HTTP method
		curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $request->method());

		// A POST, PUT or DELETE request should include the JSON data
		if(in_array($request->method(), ["POST", "PUT", "DELETE"]))
		{
			curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $request->method());
			curl_setopt($ch, CURLOPT_POST, true);
			$data = json_encode($request->all());
			curl_setopt($ch, CURLOPT_HTTPHEADER, [
				"Content-Type: application/json",
				"Content-Length: " . strlen($data)
			]);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $data);

			// TODO: Is the X-Member-Id still intact?
		}

		// Execute the cURL request and get data
		$result = curl_exec($ch);
		$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
		curl_close($ch);

		// Send response to client
		return response($result, $http_code)
			->header("Content-Type", "application/json");
	}
}