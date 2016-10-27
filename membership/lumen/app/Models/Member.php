<?php
namespace App\Models;

use App\Models\Entity;

/**
 *
 */
class Member extends Entity
{
	protected $type = "member";
	protected $join = "member";
	protected $columns = [
		"entity_id" => [
			"column" => "entity.entity_id",
			"select" => "entity.entity_id",
		],
		"created_at" => [
			"column" => "entity.created_at",
			"select" => "DATE_FORMAT(entity.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "entity.updated_at",
			"select" => "DATE_FORMAT(entity.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"description" => [
			"column" => "entity.description",
			"select" => "entity.description",
		],
		"member_number" => [
			"column" => "member.member_number",
			"select" => "member.member_number",
		],
		"email" => [
			"column" => "member.email",
			"select" => "member.email",
		],
		"password" => [
			"column" => "member.password",
			"select" => "member.password",
		],
		"reset_token" => [
			"column" => "member.reset_token",
			"select" => "member.reset_token",
		],
		"reset_expire" => [
			"column" => "member.reset_expire",
			"select" => "member.reset_expire",
		],
		"firstname" => [
			"column" => "member.firstname",
			"select" => "member.firstname",
		],
		"lastname" => [
			"column" => "member.lastname",
			"select" => "member.lastname",
		],
		"civicregno" => [
			"column" => "member.civicregno",
			"select" => "member.civicregno",
		],
		"company" => [
			"column" => "member.company",
			"select" => "member.company",
		],
		"orgno" => [
			"column" => "member.orgno",
			"select" => "member.orgno",
		],
		"address_street" => [
			"column" => "member.address_street",
			"select" => "member.address_street",
		],
		"address_extra" => [
			"column" => "member.address_extra",
			"select" => "member.address_extra",
		],
		"address_zipcode" => [
			"column" => "member.address_zipcode",
			"select" => "member.address_zipcode",
		],
		"address_city" => [
			"column" => "member.address_city",
			"select" => "member.address_city",
		],
		"address_country" => [
			"column" => "member.address_country",
			"select" => "member.address_country",
		],
		"phone" => [
			"column" => "member.phone",
			"select" => "member.phone",
		],
	];
	protected $sort = ["member_number", "desc"];
	protected $validation = [
		"firstname" => ["required"],
//		"email"     => ["required", "unique"],
	];

	public function _search($query, $search)
	{
		$words = explode(" ", $search);
		foreach($words as $word)
		{
			$query = $query->where(function($query) use($word) {
				// The phone numbers are stored with +46 in database, so strip the first zero in the phone number
				$phone = ltrim($word, "0");
				// Build the search query
				$query
					->  where("member.firstname",       "like", "%".$word."%")
					->orWhere("member.lastname",        "like", "%".$word."%")
					->orWhere("member.email",           "like", "%".$word."%")
					->orWhere("member.address_street",  "like", "%".$word."%")
					->orWhere("member.address_extra",   "like", "%".$word."%")
					->orWhere("member.address_zipcode", "like", "%".$word."%")
					->orWhere("member.address_city",    "like", "%".$word."%")
					->orWhere("member.phone",           "like", "%".$phone."%")
					->orWhere("member.civicregno",      "like", "%".$word."%")
					->orWhere("member.member_number",   "like", "%".$word."%");
			});
		}

		return $query;
	}
}