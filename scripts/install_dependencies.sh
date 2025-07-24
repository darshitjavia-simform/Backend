#!/bin/bash
set -e

echo "Installing system and Python dependencies..."
sudo apt install -y python3-venv

# install requierements
sudo su
mdkdir -p /home/ubuntu/backend-app
cd /home/ubuntu/backend-app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt
