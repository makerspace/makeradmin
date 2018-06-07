<?php

namespace App\Http\Middleware;

use Illuminate\Http\Response;
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

		// Decode the data
		if(($json = json_decode($response->getContent())) !== null)
		{
			$content = (array)$json;
		}
		else if(method_exists($response, "render"))
		{
			$content = [
				"message" => (string)$response->render()
			];
		}
		else
		{
			$content = [
				"message" => (string)$response->original
			];
		}

		// Send the well formatted response to the client
		return (new Response(
			$this->_formatJson($content),
			$status_code
		))
		->header("Content-Type", "application/json");
	}

	public function _formatJson($json)
	{
		$str = json_encode($json, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
		return "{$str}\n";
	}
}