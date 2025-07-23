#!/bin/bash
set -e

echo "Installing system and Python dependencies..."
sudo apt update -y
sudo apt install -y python3-pip jq awscli
cd /home/ubuntu/backend-app
pip3 install -r requirements.txt
