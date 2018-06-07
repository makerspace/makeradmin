<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateLoginTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("login", function (Blueprint $table)
		{
			$table->boolean("success");
			$table->integer("user_id")->nullable();
			$table->string("ip");
			$table->dateTimeTz("date")->default(DB::raw("CURRENT_TIMESTAMP"));
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("login");
	}
}