<?php
namespace App\Models;

use App\Models\Entity;

class Period extends Entity
{
	protected $type = "period";
	protected $table = "economy_accountingperiod";
	protected $id_column = "accountingperiod_id";
	protected $columns = [
		"accountingperiod_id" => [
			"column" => "economy_accountingperiod.economy_accountingperiod_id",
			"select" => "economy_accountingperiod.economy_accountingperiod_id",
		],
		"created_at" => [
			"column" => "economy_accountingperiod.created_at",
			"select" => "DATE_FORMAT(economy_accountingperiod.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "economy_accountingperiod.updated_at",
			"select" => "DATE_FORMAT(economy_accountingperiod.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "economy_accountingperiod.title",
			"select" => "economy_accountingperiod.title",
		],
		"description" => [
			"column" => "economy_accountingperiod.description",
			"select" => "economy_accountingperiod.description",
		],
		"name" => [
			"column" => "economy_accountingperiod.name",
			"select" => "economy_accountingperiod.name",
		],
		"start" => [
			"column" => "economy_accountingperiod.start",
			"select" => "DATE_FORMAT(economy_accountingperiod.start, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"end" => [
			"column" => "economy_accountingperiod.end",
			"select" => "DATE_FORMAT(economy_accountingperiod.end, '%Y-%m-%dT%H:%i:%sZ')",
		],
	];
	protected $sort = ["start", "asc"];
}