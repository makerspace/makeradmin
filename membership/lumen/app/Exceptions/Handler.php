<?php

namespace App\Exceptions;

use Exception;
use Illuminate\Validation\ValidationException;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Laravel\Lumen\Exceptions\Handler as ExceptionHandler;

class Handler extends ExceptionHandler
{
	/**
	 * A list of the exception types that should not be reported.
	 *
	 * @var array
	 */
	protected $dontReport = [
		AuthorizationException::class,
		HttpException::class,
		ModelNotFoundException::class,
		ValidationException::class,
	];

	/**
	 * Report or log an exception.
	 *
	 * This is a great spot to send exceptions to Sentry, Bugsnag, etc.
	 *
	 * @param  \Exception  $e
	 * @return void
	 */
	public function report(Exception $e)
	{
		parent::report($e);
	}

	/**
	 * Render an exception into an HTTP response.
	 *
	 * @param  \Illuminate\Http\Request  $request
	 * @param  \Exception  $e
	 * @return \Illuminate\Http\Response
	 */
	public function render($request, Exception $e)
	{
		if($e instanceof \App\Exceptions\EntityValidationException)
		{
			return Response()->json([
				"status"  => "error",
				"column"  => $e->getColumn(),
				"message" => $e->getMessage(),
			], 422);
		}
		else if($e instanceof \App\Exceptions\FilterNotFoundException)
		{
			return Response()->json([
				"status"  => "error",
				"column"  => $e->getColumn(),
				"data"    => $e->getData(),
				"message" => $e->getMessage(),
			], 404);
		}
		else if($e instanceof \Symfony\Component\HttpKernel\Exception\NotFoundHttpException)
		{
			return Response()->json([
				"status"  => "error",
				"message" => "The route you specified could not be found",
			], 404);
		}
		else
		{
			// When we're in production we want a generic error message via the API, and not a rendered HTML page
			return Response()->json([
				"status"  => "error",
				"message" => "Caught unknown exception: {$e->getMessage()}",
				"debug"   => $e->getTrace(),
			], 500);
		}
	}
}
