<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMembershipRolesTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("membership_roles", function (Blueprint $table)
		{
			$table->increments("role_id");
			$table->integer("group_id");
			$table->string("title");
			$table->text("description");
			$table->timestamps();
			$table->softDeletes();

			$table->index("group_id");
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("membership_roles");
	}
}