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
			$table->increments("instruction_id");
			$table->string("title");
			$table->text("description");

			$table->integer("instruction_number");
			$table->dateTimeTz("accounting_date");
			$table->integer("economy_category"); // TODO: Foreign key
			$table->string("importer");
			$table->string("external_id");
			$table->dateTimeTz("external_date");
			$table->string("external_text");
			$table->string("external_data");
			$table->integer("economy_verification_series"); // TODO: foreign key
			$table->integer("economy_period"); // TODO: foreign key

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
		Schema::drop("economy_instruction");
	}
}