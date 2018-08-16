<?php

namespace Makeradmin\Http\Middleware;

use Illuminate\Http\JsonResponse;
use Closure;

class Metadata
{
	/**
	 * Handle an incoming request.
	 *
	 * @param  \Illuminate\Http\Request  $request
	 * @param  \Closure  $next
	 * @param  string|null  $guard
	 * @return mixed
	 */
	public function handle($request, Closure $next, $guard = null)
	{
		$response = $next($request);

		// Parse the previous response
		$json = json_decode($response->getContent());

		// If the JSON couldn't be parsed we have to create a new empty object
		if($json === null)
		{
			$json = new \stdClass;
		}

		// Add metadata to the response
		if(!isset($json->metadata))
		{
			$json->{'metadata'} = [
				"service" => config("service.name"),
				"version" => config("service.version"),
				"date"    => date("Y-m-d\TH:i:s\Z"),
			];
		}

		// Create a new response
		return (new JsonResponse(
			$json,
			$response->getStatusCode()
		));

		return $response;
	}
}
