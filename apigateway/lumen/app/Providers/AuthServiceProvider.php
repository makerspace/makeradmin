<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Facades\Auth;
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
		Auth::extend("meep", function ($app, $name, array $config)
		{
			// Return an instance of Illuminate\Contracts\Auth\Guard...
			return new MakerGuard();
		});
	}
}