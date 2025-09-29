#!/bin/bash
# host-open.sh

# This script is called by the Python application inside the Docker container
# to open a file or directory. It relies on the Docker run command having
# mounted the X11 socket and set the DISPLAY variable for X forwarding.

# The 'xdg-open' command inside the container needs to find an application
# (like a PDF viewer or a file manager) which will then display on the host.

# We use 'nohup' to ensure the GUI application can start and detach from
# the terminal process that launched the Python app.

if [ -z "$1" ]; then
    echo "Usage: host-open.sh <file_or_directory>"
    exit 1
fi

# Use xdg-open, which is the standard way to delegate file opening.
# This assumes a minimalist viewer/browser (like 'x-www-browser' or 'evince')
# has been installed in your Docker image.
nohup xdg-open "$1" &>/dev/null &