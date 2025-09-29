#!/bin/bash

# This script runs on the host via the container's environment.
# It uses the DISPLAY variable provided by Docker to connect back to the host's X server.
# The 'nohup' (no hang up ) command ensures the host process doesn't die when the container exits.

/usr/bin/xdg-open "$@" &
