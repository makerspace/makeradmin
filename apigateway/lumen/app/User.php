<?php

namespace App;

use Illuminate\Auth\Authenticatable;
use Laravel\Lumen\Auth\Authorizable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Contracts\Auth\Authenticatable as AuthenticatableContract;
use Illuminate\Contracts\Auth\Access\Authorizable as AuthorizableContract;

// Used for Passport stuff
use League\OAuth2\Server\Entities\UserEntityInterface;
use Laravel\Passport\HasApiTokens;

class User extends Model implements AuthenticatableContract, AuthorizableContract, UserEntityInterface
{
	use Authenticatable, Authorizable, HasApiTokens;

	protected $primaryKey = "user_id";

	public function getIdentifier()
	{
		return $this->user_id;
	}
}