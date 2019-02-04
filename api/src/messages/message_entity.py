from flask import request

from membership.member_auth import hash_password
from membership.models import Member, Group
from service.api_definition import BAD_VALUE, Enum, natural1, REQUIRED
from service.db import db_session
from service.entity import Entity
from service.error import InternalServerError, UnprocessableEntity
from service.logging import logger

example = {
   "date_sent": None,
   "recipients": [
      {
         "id": 4,
         "value": "member4",
         "type": "member",
         "label": "Medlem: Anders Roos (#1003)"
      },
      {
         "type": "member",
         "label": "Medlem: Anders Roos2 (#1029)",
         "value": "member30",
         "id": 30
      }
   ],
   "message_type": "email",
   "num_recipients": 0,
   "entity_id": 0,
   "updated_at": None,
   "subject": "Hej",
   "created_at": None,
   "recipient": "",
   "message_id": 0,
   "body": "dasdasdas",
   "recipient_id": 0,
   "status": ""
}


class MessageEntity(Entity):
    
    def create(self):
        """
        Create is used to send message to a list of recipients. Recipients should be a list of objects with id,
        type where type is member or group. The rest of the data is used to create the message normally.
        """
        
        data = request.json or {}

        # Validate recipients.

        recipients = data.pop('recipients', [])
        if not isinstance(recipients, list):
            raise UnprocessableEntity("Recipients should be a list.")

        member_ids = set()
        
        for recipient in recipients:
            type_ = recipient.get('type')
            if type_ not in ('member', 'group'):
                raise UnprocessableEntity(what=BAD_VALUE, message='Recipient type should be member or group')
                
            try:
                id_ = natural1(recipient.get('id'))
            except (ValueError, TypeError):
                raise UnprocessableEntity(what=BAD_VALUE, message=f'Recipient id should be positived int.')
            
            if type_ == 'member':
                member_ids.add(id_)
            else:
                member_ids.update({i for i, in db_session.query(Member.member_id).filter(Group.group_id == id_)})
            
        message = self._create_internal(data)
        
        return self.to_obj(message)
        
# 		// Batch process members
# 		foreach(array_chunk($memberIds, $chunkSize) as $chunk)
# 		{
# 			$str_ids = implode(",", $chunk);
# //			foreach($chunk as $member_id)
# //			{
# 			// If the recipient is a member, load member from API
# 			$ch = new CurlBrowser;
# 			$ch->setHeader("Authorization", "Bearer " . config("service.bearer"));
# 			$result = $ch->call("GET", "http://" . config("service.gateway") . "/membership/member?entity_id={$str_ids}&per_page={$chunkSize}");
#
# 			// Send an error message if the API request was unsuccessful
# 			if($ch->getStatusCode() != 200)
# 			{
# 				return Response()->json([
# 					"status" => "error",
# 					"message" => "An unexpected error occured while trying to load data from the membership module",
# 				], 502);
# 			}
#
# 			// Add the member to the recipient list
# 			foreach($ch->getJson()->data as $member)
# 			{
# 				$recipientList[$member->member_id] = $member;
# 			}
# //			}
# 		}
#
# 		// Create new mail
# 		$message = new MessageModel;
# 		$message->message_type = $json["message_type"];
# 		$message->subject      = $json["message_type"] == "sms" ? $json["body"] : $json["subject"];
# 		$message->body         = $json["body"];
# 		$message->status       = "queued";
#
# 		// Validate input
# 		$message->validate();
#
# 		// Save entity
# 		$message->save();
#
# 		// Go through the recipient list and create queued messages in the database
# 		foreach($recipientList as $member)
# 		{
# 			$recipient = null;
#
# 			// Preprocess tokens
# 			$subject = $this->_proprocessTokens($json["subject"], $member);
# 			$body    = $this->_proprocessTokens($json["body"], $member);
#
# 			// Populate SMS / email
# 			if($json["message_type"] == "email")
# 			{
# 				$recipient = $member->email;
# 			}
# 			else if($json["message_type"] == "sms")
# 			{
# 				$recipient = $member->phone;
#
# 				// For SMS messages we want the subject to be equal to the content so the listing and sorting works in UI
# 				$subject = $body;
# 			}
#
# 			// Note: We queue messages even if $recipient is empty. We want still want them in the database, even if the backend are not able to send any message.
#
# 			// Create new recipient
# 			$entity = new RecipientModel;
# 			$entity->message_id = $message->entity_id;
# 			$entity->subject    = $subject;
# 			$entity->body       = $body;
# 			$entity->member_id  = $member->member_id;
# 			$entity->recipient  = $recipient;
# 			$entity->date_sent  = null;
# 			$entity->status     = "queued";
#
# 			// Validate input
# 			$entity->validate();
#
# 			// Save entity
# 			$entity->save();
# 		}
#
# 		// Send response to client
# 		return Response()->json([
# 			"status" => "created",
# 			"data" => $message->toArray(),
# 		], 201);
# 	}
#
#
# 	/**
# 	 * Load a queued/sent messages
# 	 */
# 	public function read(Request $request, $message_id)
# 	{
# 		return $this->_read("Message", [
# 			"message_id" => $message_id
# 		]);
# 	}
#
# 	/**
# 	 * todo: Preprocess all tokens in the message
# 	 */
# 	protected function _proprocessTokens($input, $member)
# 	{
# 		$input = str_replace("##expirydate##",    "2016-12-31",       $input); // todo
# 		$input = str_replace("##member_number##", $member->member_id, $input); // todo: member_number
# 		$input = str_replace("##firstname##",     $member->firstname, $input);
# 		$input = str_replace("##lastname##",      $member->lastname,  $input);
#
# 		return $input;
# 	}
# }
