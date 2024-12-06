#!/bin/bash

# Get the current directory of the script
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Load environment variables from .env file in the project root
set -o allexport
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo ".env file not found at $PROJECT_ROOT! Please create a .env file with necessary configuration."
    exit 1
fi
set +o allexport

# Check if BASE_PATH is set
if [ -z "$BASE_PATH" ]; then
    echo "BASE_PATH is not set in the .env file. Exiting..."
    exit 1
fi

# Define input and output files from environment variables
INPUT_FILE="${PROXIES_FILE:-${BASE_PATH}/input/proxies.txt}"
OUTPUT_FILE="${LIVE_PROXIES_FILE:-${BASE_PATH}/output/live_proxies.txt}"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Input file $INPUT_FILE not found! Please run fetch_proxies.sh first to collect proxies."
    exit 1
fi

# Pull Mubeng Docker image and run it to check proxies
echo "Pulling Mubeng Docker image and running it to check proxies..."
docker pull ghcr.io/kitabisa/mubeng:latest && \
docker run --rm -v "${INPUT_FILE}:/app/proxies.txt" \
    -v "$(dirname "${OUTPUT_FILE}"):/app/output" \
    ghcr.io/kitabisa/mubeng:latest \
    -f /app/proxies.txt --check --timeout 10s --goroutine 200 --verbose --output /app/output/$(basename "${OUTPUT_FILE}")

# Print a message indicating the script has completed
if [ $? -eq 0 ]; then
    echo "Live proxies have been saved to $OUTPUT_FILE"
else
    echo "Docker run failed. Please check the Docker setup and try again."
    exit 1
fi
