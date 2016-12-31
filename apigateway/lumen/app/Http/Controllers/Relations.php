<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use App\Service;
use App\Logger;
use App\Libraries\CurlBrowser;

use DB;

/**
 * Controller for the service registry
 */
class Relations extends Controller
{
	public function relations(Request $request)
	{
		$param = $request->get("param");
		$match = $request->get("matchUrl");
		$relations = $this->_getRelations($param, $match);

		// Send response
		return Response()->json([
			"data" => $relations,
		], 200);
	}

	/**
	 * Return a list of all 
	 */
	public function related(Request $request)
	{
		$param = $request->get("param");
		$match = $request->get("matchUrl");
		$from  = $request->get("from");

		$relations = $this->_getRelations($param, $match);

		$data = [];
		foreach($relations as $relation)
		{
			$data[] = $relation[1];
		}

		if(empty($data))
		{
			$result = ["data" => []];
		}
		else
		{
			// Forward params
			$params = $request->all();
			unset($params["param"]);
			unset($params["matchUrl"]);
			unset($params["from"]);

			$params["ids"] = implode(",", $data);

			$result = $this->_makeCall($from, $params);
		}

		// Send response
		return Response()->json($result, 200);
	}

	protected function _getRelations($param, $match)
	{
		$data = [];

		// Match column 1
		$urls = DB::table("relations")
			->where("url1", "=", $param)
			->pluck("url2");
		foreach($urls as $url)
		{
			$regexp = str_replace("/", "\/", $match);
			if(preg_match("/^{$regexp}$/", $url, $matches))
			{
				$data[] = $matches;
			}
		}

		// Match column 2
		$urls = DB::table("relations")
			->where("url2", "=", $param)
			->pluck("url1");
		foreach($urls as $url)
		{
			$regexp = str_replace("/", "\/", $match);
			if(preg_match("/^{$regexp}$/", $url, $matches))
			{
				$data[] = $matches;
			}
		}

		return $data;
	}

	protected function _makeCall($path, $params)
	{
		// Split the path into segments and get version + service
		$path = explode("/", $path);
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

		// Create a new url with the service endpoint url included
		$url = $service->endpoint . "/" . implode("/", $path);

		// Set query string parameters
		$ch->setQueryString($params);

		// Send the request
		$result = $ch->call("GET", $url);
		$http_code = $ch->getStatusCode();

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Send response to client
		return $ch->getJson();
	}
}