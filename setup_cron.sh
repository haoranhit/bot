#!/bin/bash

# Setup script to create a cron job for running Python bot script daily at 2:59 PM
# This script will automatically add the cron job to your crontab

echo "Setting up cron job to run Python script daily at 2:59 PM..."

# Get the current directory (where this script is located)
# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="/Users/yueqian/Downloads/code/bot"

# Define the Python script to run (change this if your main script has a different name)
PYTHON_SCRIPT="login.py"

# Check if the Python script exists
if [ ! -f "$SCRIPT_DIR/$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found in $SCRIPT_DIR"
    echo "Please make sure your Python script exists or update the PYTHON_SCRIPT variable in this setup script"
    exit 1
fi

# Create the cron job entry
# Format: 59 14 * * * (daily at 2:59 PM - 14:59 in 24-hour format)
CRON_JOB="03 23 * * * cd $SCRIPT_DIR && source venv/bin/activate && python $PYTHON_SCRIPT >> $SCRIPT_DIR/cron.log 2>&1"

# Check if this cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/$PYTHON_SCRIPT"; then
    echo "Cron job for $PYTHON_SCRIPT already exists!"
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "$SCRIPT_DIR"
    exit 0
fi

# Add the cron job to crontab
# First get existing crontab, then add new job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Verify the cron job was added
if crontab -l 2>/dev/null | grep "$SCRIPT_DIR/$PYTHON_SCRIPT"; then
    echo "✓ Cron job added successfully!"
    echo ""
    echo "Your Python script will now run daily at 2:59 PM"
    echo "Script location: $SCRIPT_DIR/$PYTHON_SCRIPT"
    echo "Log file: $SCRIPT_DIR/cron.log"
    echo ""
    echo "Useful commands:"
    echo "  View all cron jobs: crontab -l"
    echo "  Edit cron jobs: crontab -e"
    echo "  View logs: tail -f $SCRIPT_DIR/cron.log"
    echo "  Remove this cron job: crontab -e (then delete the line containing $PYTHON_SCRIPT)"
else
    echo "✗ Failed to add cron job. Please try manually:"
    echo "1. Run: crontab -e"
    echo "2. Add this line: $CRON_JOB"
    echo "3. Save and exit"
    exit 1
fi