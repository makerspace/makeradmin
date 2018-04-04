<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

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

			$table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->dateTimeTz("updated_at")->nullable();
			$table->dateTimeTz("deleted_at")->nullable();

			$table->index("role_id");
			$table->index("group_id");
		});

		DB::table("membership_groups")->insert([
			"parent" => 0,
			"left" => 0,
			"right" => 0,
			"name" => "admins",
			"title" => "Administratörer",
		]);
		$admin_group_id = DB::table("membership_groups")
			->where("name", "admins")
			->value("group_id");
		DB::table("membership_permissions")
			->insert([
				'role_id' => 2,
				'permission' => 'view group',
				'group_id' => $admin_group_id,
			]);
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
