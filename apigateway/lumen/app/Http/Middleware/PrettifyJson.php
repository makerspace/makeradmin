<?php

namespace App\Http\Middleware;
use \Illuminate\Http\Response;

use Closure;

class PrettifyJson
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
		$response = $next($request);
		$status_code = $response->getStatusCode();

		// Prettify JSON
		if($response instanceof \Illuminate\Http\JsonResponse)
		{
			// Use our own fancy class that prints it pretty!
			return new Response(
				$this->_formatJson($response->getData()),
				$status_code
			);
		}
		// The Passport stuff seems to return the JSON data as a normal Response, and not an JsonResponse
		else if(($json = json_decode($response->getContent())) !== null)
		{
			// Use our own fancy class that prints it pretty!
			return new Response(
				$this->_formatJson($json),
				$status_code
			);
		}

		if(!method_exists($response, "render"))
		{
			return new Response(
				$this->_formatJson(["message" => (string)$response->original]),
				$status_code
			);
		}

		$content = $response->render()."\n";

		return $content;
	}

	public function _formatJson($json)
	{
		$str = json_encode($json, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
		return "{$str}\n";
	}
}