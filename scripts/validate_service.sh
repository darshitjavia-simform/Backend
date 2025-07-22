#!/bin/bash
# Check if application is responding
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)

if [ "$response" = "200" ]; then
    echo "Application is running successfully"
    exit 0
else
    echo "Application failed to start"
    exit 1
fi
