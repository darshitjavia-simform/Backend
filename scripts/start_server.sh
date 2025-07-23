#!/bin/bash
set -e

cd /home/ubuntu/backend-app
echo "Starting Python backend server..."

# Load .env variables
export $(grep -v '^#' .env | xargs)

# Start app (adjust if using Gunicorn, Flask, etc.)
nohup python3 server.py > app.log 2>&1 &
