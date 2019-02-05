from membership.models import Member, Span, LABACCESS, SPECIAL_LABACESS
from multiaccess import service
from service.api_definition import GET, SERVICE
from service.db import db_session
from service.logging import logger


@service.route("/memberdata", method=GET, permission=SERVICE)
def get_memberdata():
    query = (
        db_session
            .query(Member, Span)
            .join(Span)
            .filter(Span.type.in_([LABACCESS, SPECIAL_LABACESS]),
                    Span.deleted_at.is_(None),
                    Member.deleted_at.is_(None))
    )
    
    logger.info(query)

    logger.info(query.all())
    
	# public function dumpmembers(Request $request)
	# {
	# 	$curl = new CurlBrowser;
	# 	$curl->setHeader("Authorization", "Bearer " . config("service.bearer"));
    # 
	# 	// Get all keys
	# 	$curl->call("GET", "http://" . config("service.gateway") . "/membership/key", [
	# 		"per_page" => 5000,
	# 	]);
	# 	$keys = $curl->GetJson()->data;
    # 
	# 	// Get all members with keys
	# 	$curl->call("GET", "http://" . config("service.gateway") . "/membership/member", [
	# 		'include_membership' => true,
	# 		"per_page" => 5000,
	# 	]);
    # 
	# 	$key_members = $curl->GetJson()->data;
    # 
	# 	$member_keys = [];
	# 	foreach ($key_members as $member) {
	# 		$current_member = [];
	# 		$member_id = (int) $member->member_id;
	# 		assert($member_id !== 0);
	# 		$member_number = (int) $member->member_number;
	# 		assert($member_number !== 0);
    # 
	# 		$current_member['member_id'] = $member_id;
	# 		$current_member['member_number'] = $member_number;
	# 		$current_member['firstname'] = $member->firstname;
	# 		$current_member['lastname'] = $member->lastname;
	# 		$current_member['end_date'] = $member->membership->labaccess_end;
	# 		$current_member['keys'] = [];
	# 		$member_keys[$member_id] = $current_member;
	# 	}
    # 
	# 	foreach ($keys as $key) {
	# 		$member_id = $key->member_id;
	# 		if (array_key_exists($member_id, $member_keys)) {
	# 			$current_key = [
	# 				'key_id' => $key->key_id,
	# 				'rfid_tag' => $key->tagid,
	# 			];
	# 			$member_keys[$member_id]['keys'][] = $current_key;
	# 		} else {
	# 			error_log("Key ".$key->key_id." has invalid member");
	# 		}
	# 	}
    # 
	# 	// Send response to client
	# 	return Response()->json([
	# 		"data" => array_values($member_keys),
	# 	], 200);
	# }
