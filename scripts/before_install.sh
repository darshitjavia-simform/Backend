#!/bin/bash
# Install system dependencies
apt-get update
apt-get install -y python3-pip python3-venv

# Create application directory if it doesn't exist
mkdir -p /home/ubuntu/app
cd /home/ubuntu/app

# Create virtual environment
python3 -m venv venv
