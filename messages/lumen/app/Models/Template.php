<?php
namespace App\Models;

use Makeradmin\Models\Entity;
use DB;

/**
 *
 */
class Template extends Entity
{
	protected $type = "template";
	protected $table = "messages_template";
	protected $id_column = "template_id";
	protected $soft_deletable = true;
	protected $columns = [
		"template_id" => [
			"column" => "messages_template.messages_template_id",
			"select" => "messages_template.messages_template_id",
		],
		"created_at" => [
			"column" => "messages_template.created_at",
			"select" => "DATE_FORMAT(messages_template.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "messages_template.updated_at",
			"select" => "DATE_FORMAT(messages_template.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"name" => [
			"column" => "messages_template.name",
			"select" => "messages_template.name",
		],
		"title" => [
			"column" => "messages_template.title",
			"select" => "messages_template.title",
		],
		"description" => [
			"column" => "messages_template.description",
			"select" => "messages_template.description",
		],
	];
	protected $sort = [
		["template_id", "desc"]
	];
}