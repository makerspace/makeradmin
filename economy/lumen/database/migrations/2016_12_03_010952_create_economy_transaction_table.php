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
			$table->increments("economy_transaction_id");
			$table->string("title");
			$table->text("description")->nullable();

			$table->integer("economy_instruction_id")->unsigned();
			$table->foreign("economy_instruction_id")->references("economy_instruction_id")->on("economy_instruction");

			$table->integer("economy_account_id")->unsigned();
			$table->foreign("economy_account_id")->references("economy_account_id")->on("economy_account");

			$table->integer("economy_costcenter_id")->unsigned()->nullable();
			$table->foreign("economy_costcenter_id")->references("economy_costcenter_id")->on("economy_costcenter");

			$table->integer("amount");
			$table->string("external_id")->nullable();

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
		Schema::drop("economy_transaction");
	}
}