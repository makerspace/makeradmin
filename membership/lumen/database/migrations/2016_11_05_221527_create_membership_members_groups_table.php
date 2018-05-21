<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMembershipMembersGroupsTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("membership_members_groups", function (Blueprint $table)
		{
			$table->integer("member_id");
			$table->integer("group_id");

			$table->index("member_id");
			$table->index("group_id");
			$table->unique(["member_id", "group_id"]);
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("membership_members_groups");
	}
}