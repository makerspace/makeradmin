<?php

use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

class AddSpanDeletedAt extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::table('membership_spans', function (Blueprint $table) {
			$table->softDeletesTz();
			$table->string("deletion_reason")->nullable();
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down() {
		Schema::table('membership_spans', function (Blueprint $table) {
			$table->dropColumn('deletion_reason');
			$table->dropSoftDeletesTz();
		});
	}
}