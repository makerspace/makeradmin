from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import closing
from time import sleep

from rocky.process import log_exception, stoppable
from sqlalchemy.orm import sessionmaker

from messages.models import Recipient, Message
from service.config import get_mysql_config, config
from service.db import create_mysql_engine
from service.logging import logger


def send_messages(db_session, key, domain, sender, to_override, limit):
    query = db_session.query(Recipient).join(Message)
    query = query.filter(Message.message_type == 'email', Recipient.status == 'queued')
    query = query.limit(limit)
    
    logger.info(query.all())

# 			$messages = DB::table("messages_recipient")
# 				->leftJoin("messages_message", "messages_message.messages_message_id", "=", "messages_recipient.messages_message_id")
# 				->selectRaw("messages_message.messages_message_id AS message_id")
# 				->selectRaw("messages_recipient.messages_recipient_id AS recipient_id")
# 				->selectRaw("messages_recipient.title AS subject")
# 				->selectRaw("messages_recipient.description AS body")
# 				->selectRaw("messages_recipient.recipient AS recipient")
# 				->selectRaw("messages_recipient.member_id AS member_id")
# 				->where("messages_recipient.status", "=", "queued")
# 				->where("messages_message.message_type", "=", "email")
# 				->limit($mailgun_limit)
# 				->get();
# 
# 			// Create an clean array with data
# 			$list = [];
# 			foreach($messages as $message)
# 			{
# 
# 				try {
# 					// Get the member's email
# 					$email = $message->recipient;
# 
# 					// Override recipient
# 					if (!empty($mailgun_to_override)) {
# 						$email = $mailgun_to_override;
# 						echo "Sending mail to {$message->recipient} (overriding to $email)\n";
# 					}
# 					else {
# 						echo "Sending mail to {$message->recipient}\n";
# 					}
# 
# 					// Send the mail via Mailgun
# 					$result = $mgClient->sendMessage($mailgun_domain,
# 						array(
# 							'from'    => $mailgun_from,
# 							'to'      => $email,
# 							'subject' => $message->subject,
# 							'html'    => $message->body
# 						)
# 					);
# 
# 					// Update the database and flag the E-mail as sent to this particular recipient
# 					DB::table("messages_recipient")
# 						->where("messages_recipient_id", $message->recipient_id)
# 						->update([
# 							"status"    => "sent",
# 							"date_sent" => date("Y-m-d H:i:s"),
# 						]
# 					);
# 
# 					// todo: Uppdatera status i messages
# 				}
# 				catch(\Exception $e)
# 				{
# 					DB::table("messages_recipient")
# 						->where("messages_recipient_id", $message->recipient_id)
# 						->update([
# 							"status"    => "failed",
# 							"date_sent" => date("Y-m-d H:i:s"),
# 						]
# 					);
# 
# 					// todo: Error handling
# 					echo "Error\n";
# 				}
# 			}




if __name__ == '__main__':

    with log_exception(status=1), stoppable():
        parser = ArgumentParser(description="Dispatch emails in db send queue.", 
                                formatter_class=ArgumentDefaultsHelpFormatter)
        
        parser.add_argument('--sleep', default=4, help='Sleep time (in seconds) between checking for messages to send.')
        parser.add_argument('--limit', default=10, help='Max messages to send every time checking for messages.')
        
        args = parser.parse_args()
        
        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info(f'checking for emails to send every {args.sleep} seconds, limit is {args.limit}')
        
        key = config.get('MAILGUN_KEY')
        domain = config.get('MAILGUN_DOMAIN')
        sender = config.get('MAILGUN_FROM')
        to_override = config.get('MAILGUN_TO_OVERRIDE')
        
        while True:
            with closing(session_factory()) as db_session:
                send_messages(db_session, key, domain, sender, to_override, args.limit)
            sleep(args.sleep)
            

# 		// Instantiate the Mailgunclient
# 		$mgClient = new Mailgun(config("mailgun.key"));
# 		$mailgun_domain = config("mailgun.domain");
# 		$mailgun_from = config("mailgun.from");
# 		$mailgun_to_override = config("mailgun.to");
# 		$mailgun_limit = 10;
# 
# 		while(true) {
# 			sleep(4.0);
# 
# 			// Get all messages from database
# 		}
# 	}
# }
