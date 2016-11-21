<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMembershipPermissionsTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("membership_permissions", function (Blueprint $table)
		{
			$table->increments("permission_id");
			$table->integer("role_id");
			$table->string("permission");
			$table->integer("group_id");
			$table->timestamps();
			$table->softDeletes();

			$table->index("role_id");
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
		Schema::drop("membership_permissions");
	}
}