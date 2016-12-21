<?php

namespace App\Exceptions;

use Exception;

/**
 *
 */
class FilterNotFoundException extends Exception
{
	protected $column;
	protected $data;

	function __construct($column, $data, $message)
	{
		$this->column = $column;
		$this->data = $data;
		$this->message = $message;
	}

	function getColumn()
	{
		return $this->column;
	}

	function getData()
	{
		return $this->data;
	}
}