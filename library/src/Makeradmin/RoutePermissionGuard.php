<?php

namespace Makeradmin;


use \Closure;
use Laravel\Lumen\Application;
use Makeradmin\Http\Middleware\CheckPermission;

/**
 * A wrapper for Laravel\Lumen\Application that ensure every route is assigneded a permission middleware.
 */
class RoutePermissionGuard
{
	protected $router;
	protected $default_permission;
	protected $group_permission_defined;

	public function __construct(Application $app) {
		$this->router = $app->router;
		$this->group_permission_defined = [];
		$this->default_permission = 'service';
	}

	public static function create(Application $app, $default_permission = 'service') {
		$app->routeMiddleware(['permission' => CheckPermission::class]);
		$instance = new self($app);
		$instance->default_permission = $default_permission;
		return $instance;
	}

	protected static function hasPermission(array $attributes) {
		if (
			array_key_exists('middleware', $attributes) &&
			!empty($am = $attributes['middleware']) &&
			!empty($middleware_array = is_array($am) ? $am : explode("|", $am)))
		{
			foreach ($middleware_array as $middleware){
				if (strncmp($middleware, 'permission:', strlen('permission:')) === 0 ){
					return true;
				}
			}
		}
		return false;
	}

	protected function groupPermissionDefined() {
		return end($this->group_permission_defined);
	}

	protected function ensurePermission($action){
		if ($this->groupPermissionDefined()) {
			return $action;
		} elseif (is_string($action)) {
			return ['middleware' => 'permission:'.$this->default_permission, 'uses' => $action];
		} elseif (!is_array($action)) {
			return ['middleware' => 'permission:'.$this->default_permission, $action];
		} elseif (static::hasPermission($action)) {
			return $action;
		}
		return array_merge_recursive(['middleware' => 'permission:'.$this->default_permission], $action);
	}

	/**
	 * Register a set of routes with a set of shared attributes.
	 *
	 * @param  array  $attributes
	 * @param  \Closure  $callback
	 * @return void
	 */
	public function group(array $attributes, Closure $callback)
	{
		$group_permission_defined[] = $this->groupPermissionDefined() || static::hasPermission($attributes);
		$this->router->group($attributes, function($unused) use ($callback) {
			call_user_func($callback, $this);
		});
		array_pop($group_permission_defined);
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function get($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->get($uri, $safe_action);
		return $this;
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function post($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->post($uri, $safe_action);
		return $this;
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function put($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->put($uri, $safe_action);
		return $this;
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function patch($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->patch($uri, $safe_action);
		return $this;
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function delete($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->delete($uri, $safe_action);
		return $this;
	}

	/**
	 * Register a route with the application.
	 *
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return $this
	 */
	public function options($uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->options($uri, $safe_action);
		return $this;
	}

	/**
	 * Add a route to the collection.
	 *
	 * @param  array|string  $method
	 * @param  string  $uri
	 * @param  mixed  $action
	 * @return void
	 */
	public function addRoute($method, $uri, $action)
	{
		$safe_action = $this->ensurePermission($action);
		$this->router->addRoute($method, $uri, $safe_action);
	}
}