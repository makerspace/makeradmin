<?php

return [
	'name'    => 'Economy service',
	'version' => '1.0',
	'url'     => 'economy',
	'gateway' => getenv('APIGATEWAY'),
	'bearer'  => getenv('BEARER'),
];