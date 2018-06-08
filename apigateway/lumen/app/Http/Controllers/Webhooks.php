<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use App\Service;
use Makeradmin\Logger;
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
		$ch->setHeader("Authorization", $request->header("Authorization"));
		$ch->setHeader("Stripe-Signature", $request->header("Stripe-Signature"));
		
		$post = $request->getContent();
		$ch->setHeader("Content-Type", "application/json");
		$ch->setHeader("Content-Length", strlen($post));

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