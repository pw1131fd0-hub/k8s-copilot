#!/bin/bash
cd /home/crawd_user/project/clawbook

# Clean up
pkill -f "python3 backend/main.py" 2>/dev/null
pkill -f "node server.js" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 2

# Start Backend
PYTHONPATH=. nohup python3 backend/main.py > backend.log 2>&1 &
echo "Backend started"

# Start Frontend
nohup node server.js > frontend.log 2>&1 &
echo "Frontend started"

# Start Tunnel
nohup cloudflared tunnel --url http://127.0.0.1:3003 > tunnel.log 2>&1 &
echo "Tunnel started"
