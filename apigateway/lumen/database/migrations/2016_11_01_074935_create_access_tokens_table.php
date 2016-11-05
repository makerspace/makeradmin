<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateAccessTokensTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("access_tokens", function (Blueprint $table)
		{
			$table->integer("user_id");
			$table->string("access_token", 32);
			$table->string("browser");
			$table->string("ip");
			$table->dateTimeTz("expires");

			$table->index("user_id");
			$table->unique("access_token");
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("access_tokens");
	}
}