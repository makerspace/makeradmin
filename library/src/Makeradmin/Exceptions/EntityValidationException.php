<?php

namespace Makeradmin\Exceptions;

use \Exception;

/**
 * Thrown when a Entity::validate() fails and catched in Exceptions/Handler.php to return a standardized validation error result
 */
class EntityValidationException extends Exception
{
	protected $column;

	function __construct($column, $type, $message = null)
	{
		$this->column = $column;
		if ($type == "required") {
			$this->message = "The field is required";
		} else {
			$this->message = $message;
		}
	}

	function getColumn()
	{
		return $this->column;
	}
}