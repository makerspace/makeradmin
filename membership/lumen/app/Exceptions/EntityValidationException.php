<?php

namespace App\Exceptions;

/**
 * Thrown when a Entity::validate() fails and catched in app/Exceptions/Handler.php to return a standardized validation error result
 */
class EntityValidationException extends \Exception
{
	protected $column;

	function __construct($column, $message)
	{
		$this->column = $column;
		$this->message = $message;
	}

	function getColumn()
	{
		return $this->column;
	}
}