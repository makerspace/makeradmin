<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

use DB;

use Mailgun\Mailgun;

class Send extends Command
{
	/**
	 * The console command name.
	 *
	 * @var string
	 */
	protected $signature = "service:send";

	/**
	 * The console command description.
	 *
	 * @var string
	 */
	protected $description = "Send all queued messages to the mail service provider";

	/**
	 * Execute the console command.
	 *
	 * @return void
	 */
	public function handle()
	{
		// Instantiate the Mailgunclient
		$mgClient = new Mailgun(config("mailgun.key"));
		$mailgun_domain = config("mailgun.domain");
		$mailgun_from = config("mailgun.from");
		$mailgun_to_override = config("mailgun.to");
		$mailgun_limit = 10;

		while(true) {
			sleep(4.0);

			// Get all messages from database
			$messages = DB::table("messages_recipient")
				->leftJoin("messages_message", "messages_message.messages_message_id", "=", "messages_recipient.messages_message_id")
				->selectRaw("messages_message.messages_message_id AS message_id")
				->selectRaw("messages_recipient.messages_recipient_id AS recipient_id")
				->selectRaw("messages_recipient.title AS subject")
				->selectRaw("messages_recipient.description AS body")
				->selectRaw("messages_recipient.recipient AS recipient")
				->selectRaw("messages_recipient.member_id AS member_id")
				->where("messages_recipient.status", "=", "queued")
				->where("messages_message.message_type", "=", "email")
				->limit($mailgun_limit)
				->get();

			// Create an clean array with data
			$list = [];
			foreach($messages as $message)
			{
				echo "Sending mail to {$message->recipient}\n";

				try {
					// Get the member's email
					$email = $message->recipient;

					// Override recipient
					if ($mailgun_to_override !== false) {
						$email = $mailgun_to_override;
					}

					// Send the mail via Mailgun
					$result = $mgClient->sendMessage($mailgun_domain,
						array(
							'from'    => $mailgun_from,
							'to'      => $email,
							'subject' => $message->subject,
							'html'    => $message->body
						)
					);

					// Update the database and flag the E-mail as sent to this particular recipient
					DB::table("messages_recipient")
						->where("messages_recipient_id", $message->recipient_id)
						->update([
							"status"    => "sent",
							"date_sent" => date("Y-m-d H:i:s"),
						]
					);

					// TODO: Uppdatera status i messages
				}
				catch(\Exception $e)
				{
					DB::table("messages_recipient")
						->where("messages_recipient_id", $message->recipient_id)
						->update([
							"status"    => "failed",
							"date_sent" => date("Y-m-d H:i:s"),
						]
					);

					// TODO: Error handling
					echo "Error\n";
				}
			}
		}
	}
}
