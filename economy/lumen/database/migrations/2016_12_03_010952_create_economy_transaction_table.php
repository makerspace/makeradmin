<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateEconomyTransactionTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("economy_transaction", function (Blueprint $table)
		{
			$table->increments("transaction_id");
			$table->string("title");
			$table->text("description");

			$table->integer("economy_instruction"); // TODO: foreign key
			$table->integer("economy_account"); // TODO: foreign key
			$table->integer("economy_cost_center"); // TODO: foreign key

			$table->integer("amount");
			$table->string("external_id");

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
		Schema::drop("economy_transaction");
	}
}