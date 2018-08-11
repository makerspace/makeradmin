<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateRfidTable extends Migration
{
    /**
     * Run the migrations.
     *
     * @return void
     */
    public function up()
    {
        Schema::create("membership_keys", function (Blueprint $table)
        {
            $table->increments("rfid_id");
            $table->integer('member_id')->unsigned();
            $table->foreign('member_id')->references('member_id')->on('membership_members');
            $table->text("description")->nullable();
            $table->string("tagid");

            $table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
            $table->dateTimeTz("updated_at")->nullable();
            $table->dateTimeTz("deleted_at")->nullable();

            $table->index("tagid");
        });
    }

    /**
     * Reverse the migrations.
     *
     * @return void
     */
    public function down()
    {
        Schema::drop("membership_keys");
    }
}