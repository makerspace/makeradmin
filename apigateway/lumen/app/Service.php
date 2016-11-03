<?php

namespace App;

use DB;

/**
 * TODO:
 *   All service should have an active flag? Could be useful for hotswapping services?
 *   deleted_at?
 */
class Service
{
	/**
	 * Return a service
	 */
	public static function getService($service, $version = null)
	{
		// TODO: Get the correct (or latest) version
		$result = DB::table("services")
			->where("url", "=", $service)
			->first();
		return $result ? $result : false;
	}

	/**
	 * Regiser a service
	 */
	public static function register($data)
	{
		DB::table("services")->insert($data);
	}

	/**
	 * Unregister a service
	 */
	public static function unregister($data)
	{
		DB::table("services")
			->where("url",     $data["url"])
			->where("version", $data["version"])
			->delete();
	}

	/**
	 * Get all registered services
	 */
	public static function all()
	{
		$data = DB::table("services")
			->select("service_id", "name", "url", "endpoint", "version")
			->selectRaw("DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%sZ') AS created_at")
			->selectRaw("DATE_FORMAT(updated_at, '%Y-%m-%dT%H:%i:%sZ') AS updated_at")
			->get();

		return $data;
	}
}