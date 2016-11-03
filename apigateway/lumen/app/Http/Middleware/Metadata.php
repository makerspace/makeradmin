<?php

namespace App\Http\Middleware;

use Illuminate\Http\JsonResponse;
use Illuminate\Contracts\Auth\Factory as Auth;
use Closure;

class Metadata
{
	/**
	 * The authentication guard factory instance.
	 *
	 * @var \Illuminate\Contracts\Auth\Factory
	 */
	protected $auth;

	/**
	 * Create a new middleware instance.
	 *
	 * @param  \Illuminate\Contracts\Auth\Factory  $auth
	 * @return void
	 */
	public function __construct(Auth $auth)
	{
		$this->auth = $auth;
	}

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

		// Add metadata to the response
		if(!isset($json->_meta))
		{
			$json->_meta = [
				"service" => "apigateway",
				"version" => "1.0",
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