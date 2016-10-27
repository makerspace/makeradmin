<?php
namespace App\Http\Controllers\V2;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

use App\Libraries\EconomyParserSEB;

class Economy extends Controller
{
	/**
	 *
	 */
	public function file(Request $request, $accountingperiod, $external_id, $file)
	{
//		echo "$accountingperiod {$external_id} $file";
		$file = "/var/www/html/vouchers/{$external_id}/{$file}";
		if(file_exists($file))
		{
			$finfo = finfo_open(FILEINFO_MIME_TYPE);
			$mimetype = finfo_file($finfo, $file);
			header("Content-type:$mimetype");
			echo file_get_contents($file);
		}
		else
		{
			echo "404";
		}
	}

	/**
	 *
	 */
	function importSeb()
	{
		$s = new EconomyParserSEB();
		$data = file_get_contents("/vagrant/Bokföring/Kontohändelser.csv");
		$data = $s->Import($data);

		echo "<pre>";
		print_r($data);
	}
}