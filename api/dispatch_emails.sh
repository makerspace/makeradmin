#!/bin/bash
set -e

echo "starting emaildispatcher"
exec python3 ./dispatch_emails.py
