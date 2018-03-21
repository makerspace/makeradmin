#!/bin/bash
# Exec replaces the shell with the service process which among other things allows signals to be sent directly to the service (e.g when docker wants to stop the container)
exec python3 user.py