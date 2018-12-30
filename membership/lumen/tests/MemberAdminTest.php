<?php

use Laravel\Lumen\Testing\DatabaseTransactions;

// Test the member API as an administrator
class MemberAdminTest extends TestCase
{
	// Check if the member list is empty
	public function test1()
	{
		$this
			->get("/membership/member")
			->seeJson([
				"data"         => [],
				"per_page"     => 25,
				"total"        => 0,
				"last_page"    => 0,
			])
		->assertResponseStatus(200);
	}

	// Create a member
	public function test2()
	{
		$this->json("POST", "/membership/member", [
			"email"     => "john@example.com",
			"firstname" => "John",
			"lastname"  => "Doe",
		])
		->assertResponseStatus(201);
	}

	// Check that the newly created member is in the list
	public function test3()
	{
		$this
			->get("/membership/member")
			->seeJson([
				"per_page"  => 25,
				"total"     => 1,
				"last_page" => 1,
			])
			->assertResponseStatus(200);

		$result = json_decode($this->response->getContent());

		$this->assertTrue($result->data[0]->member_id       == 1);
		$this->assertTrue($result->data[0]->email           == "john@example.com");
		$this->assertTrue($result->data[0]->firstname       == "John");
		$this->assertTrue($result->data[0]->lastname        == "Doe");
		$this->assertTrue($result->data[0]->address_country == "se");
	}

	// Load the member directly
	public function test4()
	{
		$this
			->get("/membership/member/1")
			->seeJson([
				"email"           => "john@example.com",
				"firstname"       => "John",
				"lastname"        => "Doe",
				"address_country" => "se",
			])
			->assertResponseStatus(200);
	}

	// Try to create a duplicate
	public function test5()
	{
		$this->json("POST", "/membership/member", [
			"email"     => "john@example.com",
			"firstname" => "John",
			"lastname"  => "Doe",
		])
		->seeJson([
			"status"  => "error",
			"column"  => "email",
			"message" => "The value needs to be unique in the database",
		])
		->assertResponseStatus(422);
	}

	// Create a user without a first name
	public function test6()
	{
		$this->json("POST", "/membership/member", [])
		->seeJson([
			"status"  => "error",
			"column"  => "firstname",
			"message" => "The value can not be empty",
		])
		->assertResponseStatus(422);
	}

	// Delete a member that does not exist
	public function test7()
	{
		$this->json("DELETE", "/membership/member/123", [])
		->seeJson([
			"status"  => "error",
			"message" => "Could not find any member with specified member_id",
		])
		->assertResponseStatus(404);
	}

	// Read a member that does not exist
	public function test8()
	{
		$this->get("/membership/member/123")
		->seeJson([
			"status"  => "error",
			"message" => "Could not find any member with specified member_id",
		])
		->assertResponseStatus(404);
	}

	// Soft delete the first member
	public function test9()
	{
		$this->json("DELETE", "/membership/member/1", [])
		->seeJson([
			"status" => "deleted",
		])
		->assertResponseStatus(200); //todo: Another status code
	}

	// Check that the member is deleted
	public function test10()
	{
		$this
			->get("/membership/member/1")
			->seeJson([
				"message" => "Could not find any member with specified member_id",
			])
			->assertResponseStatus(404);
	}

	// todo: Check that the member really is soft deleted
	public function test11()
	{
	}

	// Create a few members
	public function test12()
	{
		for($i = 0; $i < 200; $i++)
		{
			$this->json("POST", "/membership/member", [
				"email"     => "john_{$i}@example.com",
				"firstname" => "John",
				"lastname"  => "Doe {$i}",
			])
			->seeJson([
				"status"  => "created",
			])
			->assertResponseStatus(201);
		}
	}

	// Update member
	public function test13()
	{
		$this->json("PUT", "/membership/member/2", [
			"email" => "john@doe.com",
		])
		->seeJson([
			"status"  => "updated",
		])
		->assertResponseStatus(200);
	}

	// Check that the member got updated
	public function test14()
	{
		$this
			->get("/membership/member/2")
			->seeJson([
				"email"           => "john@doe.com",
				"firstname"       => "John",
				"lastname"        => "Doe 0",
				"address_country" => "se",
			])
			->assertResponseStatus(200);

	}

	// List all members and see that pagination is working
	public function test15()
	{
		$this
			->get("/membership/member")
			->seeJson([
				"per_page"  => 25,
				"total"     => 200,
				"last_page" => 8,
			])
			->assertResponseStatus(200);

	}

	// Search
	public function test16()
	{
		$this
			->get("/membership/member?search=Doe%2056")
			->seeJson([
				"per_page"  => 25,
				"total"     => 2,
				"last_page" => 1,
			])
			->assertResponseStatus(200);


	}

	// Sort by a column that does not exist
	public function test17()
	{
		$this
			->get("/membership/member?sort_by=magic")
			->seeJson([
				"status"  => "error",
				"column"  => "sort_by",
				"data"    => ["asc", "magic"],
				"message" => "Could not find the column you trying to sort by",
			])
			->assertResponseStatus(404);
	}

	// todo: Check that sorting is working
	// todo: Check that filtering is working
	// todo: Testa behörigheter

	public function test123()
	{
	}
}

//echo $this->response->getContent();