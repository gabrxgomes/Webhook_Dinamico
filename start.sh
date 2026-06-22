#!/usr/bin/env bash
# -------------------------------------------------------
# Starts the webhook receiver locally for development.
# Usage:
#   ./start.sh
#   CLIENT_ID=my-id CLIENT_SECRET=my-secret ./start.sh
# -------------------------------------------------------

export CLIENT_ID="${CLIENT_ID:-demo-client-id}"
export CLIENT_SECRET="${CLIENT_SECRET:-demo-client-secret}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-dev-jwt-secret-key-please-change-me}"
export TOKEN_EXPIRES_IN="${TOKEN_EXPIRES_IN:-3600}"
PORT="${PORT:-5000}"

echo ""
echo "Starting webhook receiver on port $PORT ..."
python webhook_receiver.py
