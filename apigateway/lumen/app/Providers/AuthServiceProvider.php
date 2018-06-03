<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use App\MakerGuard;

class AuthServiceProvider extends ServiceProvider
{
	/**
	 * Register any application services.
	 *
	 * @return void
	 */
	public function register()
	{
	}

	/**
	 * Boot the authentication services for the application.
	 *
	 * @return void
	 */
	public function boot()
	{
		$this->app->singleton('App\MakerGuard', function($app) {
			return new MakerGuard();
		});
	}
}