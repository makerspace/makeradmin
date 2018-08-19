<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateSpanTable extends Migration
{
    /**
     * Run the migrations.
     *
     * @return void
     */
    public function up()
    {
        Schema::create("membership_spans", function (Blueprint $table)
        {
            $table->increments("span_id");
            $table->integer('member_id')->unsigned();
            $table->foreign('member_id')->references('member_id')->on('membership_members');
            $table->date("startdate");
            $table->date("enddate");
            $table->enum('type', array('labaccess', 'membership')); // Note: modified in a later migration (add_span_type)
            $table->string("creation_reason")->nullable();
            $table->dateTimeTz("created_at")->default(DB::raw("CURRENT_TIMESTAMP"));
            $table->index("span_id");
        });
    }

    /**
     * Reverse the migrations.
     *
     * @return void
     */
    public function down()
    {
        Schema::drop("membership_spans");
    }
}