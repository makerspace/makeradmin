<?php
namespace App\Models;

use Makeradmin\Models\Entity;

/**
 *
 */
class Role extends Entity
{
	protected $type = "role";
	protected $table = "membership_roles";
	protected $id_column = "role_id";
	protected $columns = [
		"role_id" => [
			"column" => "membership_roles.role_id",
			"select" => "membership_roles.role_id",
		],
		"created_at" => [
			"column" => "membership_roles.created_at",
			"select" => "DATE_FORMAT(membership_roles.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_roles.updated_at",
			"select" => "DATE_FORMAT(membership_roles.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"group_id" => [
			"column" => "membership_roles.group_id",
			"select" => "membership_roles.group_id",
		],
		"title" => [
			"column" => "membership_roles.title",
			"select" => "membership_roles.title",
		],
		"description" => [
			"column" => "membership_roles.description",
			"select" => "membership_roles.description",
		],
	];
	protected $sort = ["title", "desc"];
	protected $validation = [
		"title"    => ["required"],
		"group_id" => ["required"],
	];
}