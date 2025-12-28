#!/bin/bash
# Airflow startup script for macOS
# Fixes segmentation fault issues on macOS

# Set environment variables to avoid macOS forking issues
export no_proxy='*'
export PYTHONFAULTHANDLER='true'
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY='YES'

# Navigate to project directory
cd "$(dirname "$0")"

echo "Starting Airflow with macOS compatibility settings..."
echo "no_proxy: $no_proxy"
echo "PYTHONFAULTHANDLER: $PYTHONFAULTHANDLER"
echo "OBJC_DISABLE_INITIALIZE_FORK_SAFETY: $OBJC_DISABLE_INITIALIZE_FORK_SAFETY"

# Start Airflow standalone
airflow standalone

