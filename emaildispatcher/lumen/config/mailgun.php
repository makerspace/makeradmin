<?php

return [
	'domain' => getenv('MAILGUN_DOMAIN'),
	'key' => getenv('MAILGUN_KEY'),
	'from'  => getenv('MAILGUN_FROM'),
	'to' => getenv('MAILGUN_TO_OVERRIDE'),
];
