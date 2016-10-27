<?php
namespace App\Models;

use App\Models\Entity;

/**
 *
 */
class Member extends Entity
{
	protected $type = "member";
	protected $table = "membership_members";
	protected $id_column = "member_id";
	protected $columns = [
		"member_id" => [
			"column" => "membership_members.member_id",
			"select" => "membership_members.member_id",
		],
		"created_at" => [
			"column" => "membership_members.created_at",
			"select" => "DATE_FORMAT(membership_members.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "membership_members.updated_at",
			"select" => "DATE_FORMAT(membership_members.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
/*
		"member_number" => [
			"column" => "member.member_number",
			"select" => "member.member_number",
		],
*/
		"email" => [
			"column" => "membership_members.email",
			"select" => "membership_members.email",
		],
		"password" => [
			"column" => "membership_members.password",
			"select" => "membership_members.password",
		],
		"reset_token" => [
			"column" => "membership_members.reset_token",
			"select" => "membership_members.reset_token",
		],
		"reset_expire" => [
			"column" => "membership_members.reset_expire",
			"select" => "membership_members.reset_expire",
		],
		"firstname" => [
			"column" => "membership_members.firstname",
			"select" => "membership_members.firstname",
		],
		"lastname" => [
			"column" => "membership_members.lastname",
			"select" => "membership_members.lastname",
		],
		"civicregno" => [
			"column" => "membership_members.civicregno",
			"select" => "membership_members.civicregno",
		],
		"company" => [
			"column" => "membership_members.company",
			"select" => "membership_members.company",
		],
		"orgno" => [
			"column" => "membership_members.orgno",
			"select" => "membership_members.orgno",
		],
		"address_street" => [
			"column" => "membership_members.address_street",
			"select" => "membership_members.address_street",
		],
		"address_extra" => [
			"column" => "membership_members.address_extra",
			"select" => "membership_members.address_extra",
		],
		"address_zipcode" => [
			"column" => "membership_members.address_zipcode",
			"select" => "membership_members.address_zipcode",
		],
		"address_city" => [
			"column" => "membership_members.address_city",
			"select" => "membership_members.address_city",
		],
		"address_country" => [
			"column" => "membership_members.address_country",
			"select" => "membership_members.address_country",
		],
		"phone" => [
			"column" => "membership_members.phone",
			"select" => "membership_members.phone",
		],
	];
	protected $sort = ["member_id", "desc"];
	protected $validation = [
		"firstname" => ["required"],
		"email"     => ["required", "unique"],
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
					->  where("membership_members.firstname",       "like", "%".$word."%")
					->orWhere("membership_members.lastname",        "like", "%".$word."%")
					->orWhere("membership_members.email",           "like", "%".$word."%")
					->orWhere("membership_members.address_street",  "like", "%".$word."%")
					->orWhere("membership_members.address_extra",   "like", "%".$word."%")
					->orWhere("membership_members.address_zipcode", "like", "%".$word."%")
					->orWhere("membership_members.address_city",    "like", "%".$word."%")
					->orWhere("membership_members.phone",           "like", "%".$phone."%")
					->orWhere("membership_members.civicregno",      "like", "%".$word."%");
//					->orWhere("membership_members.member_number",   "like", "%".$word."%");
			});
		}

		return $query;
	}
}