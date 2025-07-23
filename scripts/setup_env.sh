#!/bin/bash
set -e

echo "Setting permissions for .env file..."
chown ubuntu:ubuntu /home/ubuntu/backend-app/.env
chmod 600 /home/ubuntu/backend-app/.env
