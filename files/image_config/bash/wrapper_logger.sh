#!/bin/bash

# This is a wrapper script for logger to take -i option as the default
# If user provides -id or --id then that option takes precedence

/usr/bin/logger -i "$@"
