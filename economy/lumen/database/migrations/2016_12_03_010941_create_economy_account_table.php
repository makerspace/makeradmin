<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateEconomyAccountTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("economy_account", function (Blueprint $table)
		{
			$table->increments("economy_account_id");
			$table->string("title");
			$table->text("description")->nullable();

			$table->integer("account_number");

			$table->integer("economy_accountingperiod_id")->unsigned();
			$table->foreign("economy_accountingperiod_id")->references("economy_accountingperiod_id")->on("economy_accountingperiod");

			$table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->dateTimeTz("updated_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->softDeletes();
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("economy_account");
	}
}