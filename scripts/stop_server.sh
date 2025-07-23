#!/bin/bash
echo "Stopping Python backend..."
pkill -f app.py || true
