<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMessagesTemplateTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("messages_template", function (Blueprint $table)
		{
			$table->increments("messages_template_id");

			$table->string("name");
			$table->string("title");
			$table->text("description")->nullable();

			$table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
			$table->dateTimeTz("updated_at")->default(DB::raw("CURRENT_TIMESTAMP"));
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
		Schema::drop("messages_template");
	}
}