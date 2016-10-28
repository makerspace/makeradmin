<?php

namespace App\Http\Middleware;

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

		// Prettify JSON
		if($response instanceof \Illuminate\Http\JsonResponse)
		{
			// Use our own fancy class that prints it pretty!
			return new Meep($response->getData());
		}

		if(!method_exists($response, "render"))
		{
				return $response;
		}

		$content = $response->render()."\n";

		return $content;
	}
}
use Illuminate\Contracts\Support\Jsonable;
class Meep
{
	protected $data;

	function __construct($data)
	{
		$this->data = $data;
	}

	function __toString()
	{
		return json_encode($this->data, JSON_PRETTY_PRINT)."\n";
	}
}