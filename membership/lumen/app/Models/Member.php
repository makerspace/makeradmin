<?php
namespace App\Models;

use Makeradmin\Models\Entity;

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
		"member_number" => [
			"column" => "membership_members.member_number",
			"select" => "membership_members.member_number",
		],
		"email" => [
			"column" => "membership_members.email",
			"select" => "membership_members.email",
		],
		"password" => [
			"column" => "membership_members.password",
			"select" => "membership_members.password",
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
	protected $sort = ["member_number", "desc"];
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
					->orWhere("membership_members.civicregno",      "like", "%".$word."%")
					->orWhere("membership_members.member_number",   "like", "%".$word."%");
			});
		}

		return $query;
	}

	protected function _list($filters = [])
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery($filters);

		// Go through filters
		foreach($filters as $id => $filter)
		{
			if(is_array($filter) && count($filter) >= 2)
			{
				$op    = $filter[0];
				$param = $filter[1];
			}
			else
			{
				$op    = "=";
				$param = $filter;
			}

			// Filter on group membership
			if("group_id" == $id)
			{
				$query = $query
					->leftJoin("membership_members_groups", "membership_members_groups.member_id", "=", "membership_members.member_id")
					->where("membership_members_groups.group_id", $op, $param);
				unset($filters[$id]);
			}
		}

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$data = $query->get();

		// Prepare array to be returned
		$result = [
			"data" => $data
		];

		// Pagination
		if($this->pagination != null)
		{
			$result["total"]     = $query->getCountForPagination();
			$result["per_page"]  = $this->pagination;
			$result["last_page"] = ceil($result["total"] / $result["per_page"]);
		}

		return $result;
	}
}