#!/bin/bash
cd /home/ubuntu/app
source venv/bin/activate

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:5000 server:app --daemon --log-file=/home/ubuntu/app/gunicorn.log
