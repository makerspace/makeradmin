<?php

namespace App\Http\Middleware;

use Illuminate\Http\Response;
use Closure;
use App\Logger;

class Logging
{
	/**
	* Handle an incoming request.
	*
	* @param \Illuminate\Http\Request $request
	* @param \Closure $next
	* @return mixed
	*/
	public function handle($request, Closure $next)
	{

		// Log the request
		Logger::logRequest($request);

		// Handle the request
		$response = $next($request);

		// Log the response
		$json = json_decode($response->getContent());
		Logger::logResponse($response, $json);

		// Save log file
		Logger::save();

		return $response;
	}
}