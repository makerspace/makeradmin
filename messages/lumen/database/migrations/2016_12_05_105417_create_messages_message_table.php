<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMessagesMessageTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("messages_message", function (Blueprint $table)
		{
			$table->increments("messages_message_id");

			$table->string("title");
			$table->text("description")->nullable();

			$table->string("message_type");
			$table->string("status");

			$table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->dateTimeTz("updated_at")->default(DB::raw("CURRENT_TIMESTAMP"));
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("messages_message");
	}
}