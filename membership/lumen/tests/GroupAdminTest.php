<?php

use Laravel\Lumen\Testing\DatabaseTransactions;

// Test the group API as an administrator
class GroupAdminTest extends TestCase
{
/*
	// Check if the group list is empty
	public function test1()
	{
		$this
			->get("/group")
			->seeJson([
				"data"         => [],
				"per_page"     => 25,
				"total"        => 0,
				"last_page"    => 0,
			])
		->assertResponseStatus(200);
	}

	// Create a group
	public function test2()
	{
		$this->json("POST", "/group", [
			"title"       => "New group",
			"description" => "This group is fancy!",
//			"parent"      => 1
		])
		->assertResponseStatus(201);
	}

	// Check that the newly created group is in the list
	public function test3()
	{
		$this
			->get("/group")
			->seeJson([
				"per_page"  => 25,
				"total"     => 1,
				"last_page" => 1,
			])
			->assertResponseStatus(200);

		$result = json_decode($this->response->getContent());

		$this->assertTrue($result->data[0]->parent      == null);
		$this->assertTrue($result->data[0]->title       == "New group");
		$this->assertTrue($result->data[0]->description == "This group is fancy!");
	}

	// Load the group directly
	public function test4()
	{
		$this
			->get("/group/1")
			->seeJson([
				"parent"      => null,
				"title"       => "New group",
				"description" => "This group is fancy!",
			])
			->assertResponseStatus(200);
	}

	// Create a group without a title
	public function test5()
	{
		$this->json("POST", "/group", [])
		->seeJson([
			"status"  => "error",
			"column"  => "title",
			"message" => "The value can not be empty",
		])
		->assertResponseStatus(422);
	}
*/

	// Delete a group that does not exist
	public function test6()
	{
		$this->json("DELETE", "/group/123", [
		])
		->seeJson([
			"status"  => "error",
			"message" => "No group with specified group_id",
		])
		->assertResponseStatus(404);
	}

	// Read a group that does not exist
	public function test7()
	{
		$this->get("/group/123")
		->seeJson([
			"status"  => "error",
			"message" => "No group with specified group_id",
		])
		->assertResponseStatus(404);
	}
}