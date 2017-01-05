<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;
use App\Libraries\CurlBrowser;

class Facade extends Controller
{
	public function index(Request $request)
	{
		return Response()->json([
			"data" => "todo: facades",
		], 200);
	}
}