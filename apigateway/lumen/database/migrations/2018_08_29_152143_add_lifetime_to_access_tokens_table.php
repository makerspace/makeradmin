<?php
use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

class AddLifetimeToAccessTokensTable extends Migration {

	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up() {
		Schema::table('access_tokens', function (Blueprint $table) {
			$table->unsignedInteger('lifetime')->default(300);
		});

		DB::table('access_tokens')
		->where('user_id', ">", 0)
		->update([
			'lifetime' => 1209600,
			'expires' => DB::raw("DATE_ADD(NOW(), INTERVAL 1209600 SECOND)"),
		]);

		DB::table('access_tokens')
		->where('user_id', -1)
		->update([
			'lifetime' => 315360000,
			'expires' => DB::raw("DATE_ADD(NOW(), INTERVAL 315360000 SECOND)"),
		]);
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down() {
		Schema::table('access_tokens', function (Blueprint $table) {
			$table->dropColumn(['lifetime']);
		});
	}
}
