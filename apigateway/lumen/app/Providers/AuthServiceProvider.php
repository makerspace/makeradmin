<?php

namespace App\Providers;

use App\User;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Facades\Auth;

use League\OAuth2\Server\AuthorizationServer;
use League\OAuth2\Server\Grant\PasswordGrant;

class AuthServiceProvider extends ServiceProvider
{
	/**
	 * Register any application services.
	 *
	 * @return void
	 */
	public function register()
	{
		$this->app->singleton(AuthorizationServer::class, function()
		{
			return tap($this->makeAuthorizationServer(), function($server)
			{
				$server->enableGrantType(
					$this->makePasswordGrant(), \Laravel\Passport\Passport::tokensExpireIn()
				);
			});
		});
	}

	/**
	 * Boot the authentication services for the application.
	 *
	 * @return void
	 */
	public function boot()
	{
		// Here you may define how you wish users to be authenticated for your Lumen
		// application. The callback which receives the incoming request instance
		// should return either a User instance or null. You're free to obtain
		// the User instance via an API token or any other method necessary.
/*
		$this->app['auth']->viaRequest('api', function ($request) {
			if ($request->input('api_token')) {
				return User::where('api_token', $request->input('api_token'))->first();
			}
		});
*/
	}

	public function makeAuthorizationServer()
	{
		return new AuthorizationServer(
			$this->app->make(\Laravel\Passport\Bridge\ClientRepository::class),
			$this->app->make(\Laravel\Passport\Bridge\AccessTokenRepository::class),
			$this->app->make(\Laravel\Passport\Bridge\ScopeRepository::class),
			'file://'.\Laravel\Passport\Passport::keyPath('oauth-private.key'),
			'file://'.\Laravel\Passport\Passport::keyPath('oauth-public.key')
		);
	}

	protected function makePasswordGrant()
	{
		$grant = new PasswordGrant(
			$this->app->make(UserRepository::class),
			$this->app->make(\Laravel\Passport\Bridge\RefreshTokenRepository::class)
		);

		$grant->setRefreshTokenTTL(\Laravel\Passport\Passport::refreshTokensExpireIn());

		return $grant;
	}
}


use RuntimeException;
use Illuminate\Contracts\Hashing\Hasher;
use League\OAuth2\Server\Entities\ClientEntityInterface;
use League\OAuth2\Server\Repositories\UserRepositoryInterface;

class UserRepository implements UserRepositoryInterface
{
	/**
	 * The hasher implementation.
	 *
	 * @var \Illuminate\Contracts\Hashing\Hasher
	 */
	protected $hasher;

	/**
	 * Create a new repository instance.
	 *
	 * @param  \Illuminate\Contracts\Hashing\Hasher  $hasher
	 * @return void
	 */
	public function __construct(Hasher $hasher)
	{
		$this->hasher = $hasher;
	}

	/**
	 * {@inheritdoc}
	 */
	public function getUserEntityByUserCredentials($username, $password, $grantType, ClientEntityInterface $clientEntity)
	{
		// TODO: Skicka request till /membership för att autentisera användare
		if(true)
		{
			$user_id = 18;
		}
		else
		{
			return false;
		}

		// Check that the user is in our local database and create a new one if not
		$user = User::where("user_id", $user_id)->first();
		echo "User:\n";
		print_r($user);
		if(!$user)
		{
			$user = new User();
			$user->user_id = $user_id;
			$user->save();
		}

		// Return the user
		return $user;
	}
}