<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateEconomyInstructionTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("economy_instruction", function (Blueprint $table)
		{
			$table->increments("economy_instruction_id");
			$table->string("title");
			$table->text("description")->nullable();

			$table->integer("instruction_number")->nullable();
			$table->dateTimeTz("accounting_date")->nullable();

			$table->integer("economy_category_id")->unsigned()->nullable();
			$table->foreign("economy_category_id")->references("economy_category_id")->on("economy_category");

			$table->string("importer")->nullable();
			$table->string("external_id")->nullable();
			$table->dateTimeTz("external_date")->nullable();
			$table->string("external_text")->nullable();
			$table->string("external_data")->nullable();

			$table->integer("economy_verificationseries_id")->unsigned()->nullable();
			$table->foreign("economy_verificationseries_id")->references("economy_verificationseries_id")->on("economy_verificationseries");

			$table->integer("economy_accountingperiod_id")->unsigned()->nullable();
			$table->foreign("economy_accountingperiod_id")->references("economy_accountingperiod_id")->on("economy_accountingperiod");

			$table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->dateTimeTz("updated_at")->nullable();
			$table->dateTimeTz("deleted_at")->nullable();
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("economy_instruction");
	}
}