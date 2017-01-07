<?php
namespace App\Http\Controllers;

//use App\Http\Controllers\Controller;
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
	public function createRelation(Request $request)
	{
		DB::table("relations")
			->insert([
				"url1" => $request->get("url1"),
				"url2" => $request->get("url2"),
			]);

		// Send response
		return Response()->json([
			"status" => "ok",
		], 200);
	}

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

		// Extract a list of id's
		$data = [];
		foreach($relations as $relation)
		{
			$data[] = $relation["matches"][1];//TODO
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

			$params["entity_id"] = implode(",", $data);

			$result = $this->_makeCall($from, $params);
		}

		// Send response
		return Response()->json($result, 200);
	}

	protected function _getRelations($param, $match)
	{
		$data = [];
		$regexp = str_replace("/", "\/", $match);

		// Match column 1
		$relations = DB::table("relations")
			->where("url1", "LIKE", $param)
			->select("url1", "url2")
			->get();
		foreach($relations as $relation)
		{
			if(preg_match("/^{$regexp}$/", $relation->url2, $matches))
			{
				$data[] = [
					"url"     => $relation->url1,
					"matches" => $matches
				];
			}
		}

		// Match column 2
		$relations = DB::table("relations")
			->where("url2", "LIKE", $param)
			->select("url1", "url2")
			->get();
		foreach($relations as $relation)
		{
			if(preg_match("/^{$regexp}$/", $relation->url1, $matches))
			{
				$data[] = [
					"url"     => $relation->url2,
					"matches" => $matches
				];
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

		// Send the request
		$result = $ch->call("GET", $url, $params);
		$http_code = $ch->getStatusCode();

		// Log the internal HTTP request
		Logger::logServiceTraffic($ch);

		// Send response to client
		return $ch->getJson();
	}
}
