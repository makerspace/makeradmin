<?php

return [
	'name'    => 'Messages service',
	'version' => '1.0',
	'url'     => 'messages',
	'gateway' => getenv('APIGATEWAY'),
	'bearer'  => getenv('BEARER'),
];