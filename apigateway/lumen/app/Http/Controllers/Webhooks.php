<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use Makeradmin\Exceptions\EntityValidationException;
use App\Service;
use Makeradmin\Logger;
use Makeradmin\SecurityHelper;
use Makeradmin\Libraries\CurlBrowser;

/**
 * Controller for external webhooks
 */
class Webhooks extends Controller
{
	/**
	 * Handle callback from stripe
	 */
	public function stripe(Request $request)
	{
		$version = 1;// TODO: Get version from header
		// Get the endpoint URL or throw an exception if no service was found
		if(($service = Service::getService("webshop", $version)) === false)
		{
			throw new NotFoundHttpException;
		}
		
		// Initialize cURL
		$ch = new CurlBrowser;
		foreach($request->headers as $name => $value){
			$ch->setHeader($name, $value);
		}

		$post = $request->getContent();
			
		// Forward the content-type
		$ch->setHeader("Content-Type", $request->header("Content-Type"));

		// Create a new url with the service endpoint url included
		$url = $service->endpoint . $request->path();
		
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
}