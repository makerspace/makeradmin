<?php

return [
	'disks' => [
		'logs' => [
			'driver' => 'local',
			'root'   => storage_path().'/logs/json',
		],
	],
];