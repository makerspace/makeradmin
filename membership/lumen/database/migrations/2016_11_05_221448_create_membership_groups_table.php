<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMembershipGroupsTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("membership_groups", function (Blueprint $table)
		{
			$table->increments("group_id");
			$table->integer("parent");
			$table->integer("left");
			$table->integer("right");
			$table->string("title");
			$table->text("description");
			$table->timestamps();
			$table->softDeletes();

			$table->index("parent");
			$table->index("left");
			$table->index("right");
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("membership_groups");
	}
}