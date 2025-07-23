#!/bin/bash
echo "Stopping Python backend..."
pkill -f server.py || true
