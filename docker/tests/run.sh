#!/bin/bash

# Exit on any error
set -e

# Parse command line arguments
USE_EXISTING=false
for arg in "$@"; do
    case $arg in
        --use-existing)
            USE_EXISTING=true
            shift
            ;;
        *)
            # Unknown option
            echo "Usage: $0 [--use-existing]"
            echo "  --use-existing  Use existing Docker Compose setup instead of starting/stopping services"
            exit 1
            ;;
    esac
done

echo "Setting up Python virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate
echo "Virtual environment activated."

# Install dependencies
echo "Installing dependencies..."
pip install -r ../requirements.txt
pip install -r test-requirements.txt

# Set environment variable if using existing setup
if $USE_EXISTING; then
    echo "Using existing Docker Compose setup..."
    export SKIP_DOCKER_SETUP=true
fi

# Run tests
echo "Running tests..."
python test.py

echo "Tests completed."
