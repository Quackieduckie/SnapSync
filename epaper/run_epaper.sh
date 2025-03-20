#!/bin/bash

# Activate the virtual environment
source "$(dirname "$0")/epaper-env/bin/activate"

# Run the system stats script
python "$(dirname "$0")/system_stats_v8.2.py"

# Deactivate the virtual environment when done
deactivate

