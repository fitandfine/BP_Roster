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

echo "Attempting to open file on Host: $1"

# Use xdg-open, which is the standard way to delegate file opening.
# We have removed the error suppression to make debugging possible.
# The output (including errors) will now print to the terminal.
nohup xdg-open "$1" &