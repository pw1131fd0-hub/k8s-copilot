#!/bin/bash
# ClawBook supervisor - keeps frontend and tunnel alive
LOG="/home/crawd_user/project/clawbook/supervisor.log"

log() { echo "[$(date)] $1" >> $LOG; }

log "Supervisor starting"

while true; do
    # Keep frontend alive
    if ! pgrep -f "node server.js" > /dev/null 2>&1; then
        log "Frontend dead, restarting..."
        cd /home/crawd_user/project/clawbook
        node server.js >> /dev/null 2>&1 &
    fi

    # Keep backend alive
    if ! pgrep -f "python3 backend/main.py" > /dev/null 2>&1; then
        log "Backend dead, restarting..."
        cd /home/crawd_user/project/clawbook
        PYTHONPATH=. python3 backend/main.py >> /dev/null 2>&1 &
    fi

    # Keep tunnel alive
    if ! pgrep -f "cloudflared tunnel" > /dev/null 2>&1; then
        log "Tunnel dead, restarting..."
        cd /home/crawd_user/project/clawbook
        cloudflared tunnel --url http://127.0.0.1:3003 >> tunnel_sup.log 2>&1 &
    fi

    sleep 10
done
