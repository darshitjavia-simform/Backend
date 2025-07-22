#!/bin/bash
cd /home/ubuntu/app

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Set environment variables from SSM and Secrets Manager
export DB_CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id dev-db-credentials-00 --query 'SecretString' --output text)
export DB_USER=$(echo $DB_CREDENTIALS | jq -r '.username')
export DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
export DB_HOST=$(aws ssm get-parameter --name /dev/db/endpoint --query 'Parameter.Value' --output text)
