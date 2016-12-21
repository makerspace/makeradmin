<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMessagesRecipientTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("messages_recipient", function (Blueprint $table)
		{
			$table->increments("messages_recipient_id");

			$table->integer("messages_message_id")->unsigned();
			$table->foreign("messages_message_id")->references("messages_message_id")->on("messages_message");

			$table->string("title");
			$table->text("description")->nullable();

			$table->integer("member_id")->nullable();
			$table->string("recipient")->nullable();
			$table->dateTimeTz("date_sent")->nullable();
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
		Schema::drop("messages_recipient");
	}
}