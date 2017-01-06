<?php

namespace App\Libraries;

use \DOMDocument;
use \DOMXPath;
use \Exception;

class CurlBrowser
{
	private $curl_handle;
	private $http_code = null;
	private $html = null;
	private $verbose = 1;
	private $allowAllHttpCodes = true;
	private $json = false;
	private $headers = [];
	private $runTime = 0;
	private $url = "";
	private $method = "GET";
	private $queryString = [];
	private $data = null;
	private $responseHeaders = [];

	/**
	 * Initialize curl and use cookies
	 *
	 * @todo Unique name for cookie files
	 */
	public function __construct()
	{
		$this->curl_handle = curl_init();
		curl_setopt($this->curl_handle, CURLOPT_RETURNTRANSFER, true);
//		curl_setopt($this->curl_handle, CURLOPT_COOKIEFILE, "cookiefile.txt");
//		curl_setopt($this->curl_handle, CURLOPT_COOKIEJAR,  "cookiefile.txt");
//		curl_setopt($this->curl_handle, CURLOPT_USERAGENT,  "Mozilla/5.0 (Windows NT 6.1; rv:46.0) Gecko/20100101 Firefox/46.0 ID:20160502172042");

		// This one is needed for the SEB stuff. Does is fuck up something else?
		curl_setopt($this->curl_handle, CURLOPT_FOLLOWLOCATION, true);

		// Include response headers
		curl_setopt($this->curl_handle, CURLOPT_HEADER, true);

		if($this->verbose >= 3)
		{
		curl_setopt($this->curl_handle, CURLOPT_VERBOSE, true);
		}
	}

	/**
	 * Close the curl handler when the object is destructed
	 */
	public function __destruct()
	{
		curl_close($this->curl_handle);
	}

	/**
	 *
	 */
	function destroy()
	{
		curl_close($this->curl_handle);
	}

	/**
	 *
	 */
	function Log($message, $verbose_level = 1)
	{
		if($this->verbose >= $verbose_level)
		{
			$date = date("c");
			echo "[{$date}] {$message}\n";
		}
	}

	/**
	 *
	 */
	public function setReferer($url)
	{
		curl_setopt($this->curl_handle, CURLOPT_REFERER, $url);
	}

	/**
	 *
	 */
	public function call($method, $url, array $qs = [], $post = [])
	{
		// Set query string parameters
		$this->queryString = [];
		foreach($qs as $key => $value)
		{
			$this->queryString[$key] = $value;
		}

		// GET, POST, etc
		curl_setopt($this->curl_handle, CURLOPT_CUSTOMREQUEST, $method);

		// A POST, PUT or DELETE request should include the POST data
		if(in_array($method, ["POST", "PUT", "DELETE"]))
		{
			$this->data = $post;
			curl_setopt($this->curl_handle, CURLOPT_POST, true);
			if($this->json === true)
			{
				$dataStr = json_encode($post);
				$this->setHeader("Content-Type", "application/json");
				$this->setHeader("Content-Length", strlen($dataStr));
			}
			else if(is_array($post))
			{
				$dataStr = http_build_query($post, "", "&");
			}
			else
			{
				$dataStr = $post;
			}
			curl_setopt($this->curl_handle, CURLOPT_POSTFIELDS, $dataStr);
		}
		else
		{
			curl_setopt($this->curl_handle, CURLOPT_POST, false);

		}

		// Set the URL
		$this->url = $url;

		// Execute the query and measure time
		$t1 = microtime(true);
		$this->html = $this->_exec();
		$t2 = microtime(true);
		$this->runTime = round(($t2 - $t1) * 1000);

		// Save information for later use
		$this->method = $method;
		$this->http_code = curl_getinfo($this->curl_handle, CURLINFO_HTTP_CODE);

		// Return data
		return $this->html;
	}

	/**
	 * HTTP POST request
	 */
	public function Post($url, $post, $json = false)
	{
		$this->Log("POST {$url}\n$data", 3);

		// Execute the request
		try
		{
			$this->html = $this->_exec();
			$this->Log("Received {$this->html}", 3);
		}
		catch(Exception $e)
		{
			echo "Error: ".$e->GetMessage()."\n";
		}

		// Check HTTP status code
		$this->_checkStatusCode();
	}

	/**
	 * Return the time i milliseconds it took to run the request
	 */
	public function runTime()
	{
		return $this->runTime;
	}

	/**
	 * Tell the library to JSON encode the POST data
	 */
	public function useJson()
	{
		$this->json = true;
	}

	/**
	 * The returned data is supposed to be a JSON array. Parse it and return it as an PHP array
	 */
	public function getJson()
	{
		$json = json_decode($this->html);
		if(!empty((array)$json))
		{
			return $json;
		}
		else
		{
			return false;
		}
	}

	/**
	 * Return POST data
	 */
	public function getData()
	{
		return $this->data;
	}

	/**
	 * Return the latest HTTP status code
	 */
	public function getStatusCode()
	{
		return $this->http_code;
	}

	/**
	 * Return the HTTP headers from the response
	 */
	public function getResponseHeaders()
	{
		return $this->responseHeaders;
	}

	/**
	 * Get the currently set URL
	 */
	public function getMethod()
	{
		return $this->method;
	}

	/**
	 * Get the currently set URL
	 */
	public function getUrl()
	{
		return $this->url;
	}

	/**
	 * Set an HTTP header
	 */
	public function setHeader($name, $value)
	{
		$this->headers[$name] = $value;
	}

	/**
	 * Return all request headers as an array
	 */
	public function getHeaders()
	{
		return $this->headers;
	}

	/**
	 * Set the query string parameters
	 */
	public function setQueryString($a = null, $b = null)
	{
		if(func_num_args() == 1)
		{
			foreach(func_get_arg(0) as $key => $value)
			{
				$this->queryString[$key] = $value;
			}
		}
		else
		{
			$this->queryString[func_get_arg(0)] = func_get_arg(1);
		}
	}

	/**
	 * Return the query string parameters used in the request
	 */
	public function getQueryString()
	{
		return $this->queryString;
	}

	/**
	 * Execute the cURL request
	 */
	private function _exec()
	{
		// Process HTTP headers
		$headers = [];
		foreach($this->headers as $key => $value)
		{
			$headers[] = "{$key}: {$value}";
		}
		curl_setopt($this->curl_handle, CURLOPT_HTTPHEADER, $headers);

		// Process query string
		$querystring = http_build_query($this->queryString, "", "&");
		$url = $this->url;
		if(!empty($querystring))
		{
			// Prepent the query string to the URL
			$url .= "?{$querystring}";
		}

		// Set URL
		curl_setopt($this->curl_handle, CURLOPT_URL, $url);

		// Run the query
		$result = curl_exec($this->curl_handle);

		// Split the result into header and body
		$header_size = curl_getinfo($this->curl_handle, CURLINFO_HEADER_SIZE);
		$this->html = substr($result, $header_size);

		// Split the response headers into an array
		$temp = str_replace("\r", "", substr($result, 0, $header_size));
		$headers = explode("\n", $temp);

		// Remove the first line (GET / HTTP/1.1)
		array_shift($headers);

		// Go through all other lines
		foreach($headers as $header)
		{
			// Ignore the empty newlines at the end
			if(empty($header))
			{
				continue;
			}

			// Split header on :
			$segments = explode(":", $header);

			// First segment is header name
			$key = array_shift($segments);

			// All other segments are value
			$value = implode("", $segments);

			// Save the header
			$this->responseHeaders[$key] = $value;
		}

		// Return body
		return $this->html;
	}

	/**
	 * Parse the HTML into A DOM and return a new DOMXPath object
	 */
	public function getXPath()
	{
		$page = new DOMDocument();
		@$page->loadHTML($this->html);
		return new DOMXPath($page);
	}

	private function _checkStatusCode()
	{
		// Check HTTP status code
		if($this->http_code == 200)
		{
			// A 200 means everything went OK
			return true;
		}
		else if($this->http_code == 302)
		{
			// A 302 means a redirect, then we should save the URL
			$this->last_url = curl_getinfo($this->curl_handle, CURLINFO_EFFECTIVE_URL);
			echo "Redirect: {$this->last_url}\n";
		}
		else if(!$this->allowAllHttpCodes)
		{
			// Other status codes should throw an error
			echo $this->html;
			throw(new Exception("Received a {$this->http_code} HTTP status code. Expected a 200 or 302 from server."));
		}
	}
}