<?php

namespace Makeradmin\Exceptions;

use \Exception;

/**
 * Thrown when a Entity::validate() fails and catched in Exceptions/Handler.php to return a standardized validation error result
 */
class EntityValidationException extends Exception
{
	protected $column;
	protected $type;

	function __construct($column, $type, $message = null)
	{
		$this->column = $column;
		$this->type = $type;
		if ($type == "required") {
			$this->message = "The field is required";
		} else if ($type == "unique") {
			$this->message = "The value needs to be unique in the database";
		} else {
			$this->message = $message;
		}
	}

	function getColumn()
	{
		return $this->column;
	}

	function getType()
	{
		return $this->type;
	}
}