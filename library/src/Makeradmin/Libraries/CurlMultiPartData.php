<?php

namespace Makeradmin\Libraries;

class CurlMultiPartData
{
	private $data;

	public function __construct($data){
		$this->data = $data;
	}

	public function post_fields(): array {
		// TODO: Handle more than files key and verify file handling
		$post_fields = [];
		foreach($this->data as $key => $value) {
			if('files' == $key){
				if (is_array($value)) {
					$i = 0;
					foreach($value as $v) {
						$post_fields["files[{$i}]"] = curl_file_create((string)$v, $v->getClientMimeType(), $v->getClientOriginalName());
						$i++;
					}
				} else {
					$post_fields['files[0]'] = curl_file_create((string)$value, $value->getClientMimeType() ,$value->getClientOriginalName());
				}
			}else{
				throw new \Exception("Unimplemented key ".$key);
			}
		}
		return $post_fields;
	}
}
