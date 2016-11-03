<?php

namespace App;

use Illuminate\Support\Facades\Storage;

/**
 * Logger used for logging all HTTP traffic (with debug information) into JSON files.
 */
class Logger
{
	private static $data;
	private static $filename;

	/**
	 * Log an Request object
	 */
	public static function logRequest($request)
	{
		// Get date
		$date = static::timestamp();

		// Create a filename used when saving the log
		static::$filename = $date."_".$_SERVER["REMOTE_ADDR"]."_".$_SERVER["REQUEST_METHOD"].".json";

		// Create an array with basic information
		static::$data = [
			"ip"   => $_SERVER["REMOTE_ADDR"],
			"host" => $_SERVER["HTTP_HOST"],
			"request" => [
				"date"       => $date,
				"method"     => $_SERVER["REQUEST_METHOD"],
				"url"        => $request->path(),
				"headers"    => static::_compactHeaders($request->headers->all()),
				"query"      => $request->query->all(),
			],
		];

		// The query string parameters should not be included as it already is in $data["query"]
		if($_SERVER["REQUEST_METHOD"] != "GET")
		{
			static::$data["request"]["data"] = $request->request->all();
		}
	}

	/**
	 * Log an Response object
	 */
	public static function logResponse($response, $content)
	{
		static::$data["response"] = [
			"date"    => static::timestamp(),
			"status"  => $response->getStatusCode(),
			"headers" => static::_compactHeaders($response->headers->all()),
			"data"    => $content,
		];
	}

	/**
	 * Log all traffic to and from the micro service
	 */
	public static function logServiceTraffic($ch)
	{
		// Log both request and response from the internal micro service HTTP request
		static::$data["serviceTraffic"] = [
			"timeEllapsed" => $ch->runTime(),
			"request" => [
				"method"  => $ch->getMethod(),
				"url"     => $ch->getUrl(),
				"headers" => $ch->getHeaders(),
				"query"   => $ch->getQueryString(),
				"data"    => $ch->getData(),
			],
			"response" => [
				"status"  => $ch->getStatusCode(),
				"headers" => $ch->getResponseHeaders(),
				"data"    => $ch->getJson(),
			],
		];
	}

	/**
	 * Return all data that should be logged
	 */
	public static function data()
	{
		return static::$data;
	}

	/**
	 * Save the log into a JSON file
	 */
	public static function save()
	{
		$str = json_encode(static::$data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
		$str .= "\n";
		Storage::disk("logs")->put(static::$filename, $str);
	}

	/**
	 * Create a ISO8601 date with microseconds and UTC
	 */
	protected static function timestamp()
	{
		// Microtime will not return any decimals if it runs on an exact second
		$now = number_format(microtime(true), 6, '.', '');

		// Create and format timestamp
		$date = \DateTime::createFromFormat("U.u", $now);
		$date->setTimezone(new \DateTimeZone("UTC"));
		return $date->format("Y-m-d\TH:i:s.u\Z");
	}

	/**
	 * Make headers into a more compact array
	 */
	protected static function _compactHeaders($headers)
	{
		// Make headers into a more compact array
		$result = [];
		foreach($headers as $key => $values)
		{
			$result[$key] = implode(", ", $values);
		}
		return $result;
	}
}