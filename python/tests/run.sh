#!/bin/bash

# Exit on any error
set -e

# Parse command line arguments
MANAGE_DOCKER=false
TEST_PROFILE="docker"
for arg in "$@"; do
    case $arg in
        --manage-docker)
            MANAGE_DOCKER=true
            shift
            ;;
        --profile=*)
            TEST_PROFILE="${arg#*=}"
            shift
            ;;
        *)
            # Unknown option
            echo "Usage: $0 [--manage-docker] [--profile=docker|kubernetes]"
            echo "  --manage-docker  Start/stop Docker Compose services (default: use existing setup)"
            echo "  --profile        Test profile to use (default: docker)"
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

# Set environment variables
export TEST_PROFILE
if $MANAGE_DOCKER; then
    export MANAGE_DOCKER=true
fi

# Run tests
echo "Running tests with profile: $TEST_PROFILE"
python test.py

echo "Tests completed."
