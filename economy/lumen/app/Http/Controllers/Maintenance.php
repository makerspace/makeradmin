<?php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use DB;

class Maintenance extends Controller
{
	/**
	 * Returns all instructions where the sum of all transactions is not zero.
	 */
	function unbalancedInstructions(Request $request)
	{
		$query = "SELECT economy_instruction.*, SUM(economy_transaction.amount) AS meep " .
		         "FROM economy_instruction " .
		         "JOIN economy_transaction " .
		         "ON economy_transaction.economy_instruction_id = economy_instruction.economy_instruction_id " .
		         "GROUP BY economy_instruction_id " .
		         "HAVING meep != 0";
		$result = DB::select($query);

		return Response()->json([
			"unbalanced_instructions" => $result,
		], 200);
	}

	/**
	 * This function updates the instruction numbers on all instructions except number 0.
	 */
	function updateInstructionNumbers(Request $request)
	{
		DB::statement("SET @number = 0;");

		$result = DB::statement(
			"UPDATE economy_instruction " .
			"SET instruction_number = (@number :=  1 + @number) " .
			"WHERE instruction_number != 0 OR instruction_number IS NULL " .
			"ORDER BY accounting_date"
		);

		return Response()->json([
			"status" => $result,
		], 200);
	}
}