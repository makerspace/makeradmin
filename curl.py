#!/usr/bin/python3
import argparse
import backend.src.backend_service as service
import json

gateway = service.gateway_from_envfile(".env")
parser = argparse.ArgumentParser(description='Send requests to MakerAdmin')
parser.add_argument("--type", choices=["GET", "POST"], required=True)
parser.add_argument("--url", required=True)
parser.add_argument("--data", required=False)
args = parser.parse_args()

if args.type == "GET":
	r = gateway.get(args.url)
elif args.type == "POST":
	r = gateway.post(args.url, json.loads(args.data) if args.data is not None else {})

print(r.status_code)
print(r.text)
