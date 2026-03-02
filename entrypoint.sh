#!/bin/sh
# Docker entrypoint script supporting `serve` and `smoke` commands.
# Usage:
#   docker run IMAGE serve   -- start the MCP server on port 8000
#   docker run IMAGE smoke   -- run a quick health/readiness check

set -e

COMMAND="${1:-serve}"

case "$COMMAND" in
  serve)
    echo "Starting FastAPI MCP Server on port 8000..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  smoke)
    echo "Running smoke check..."
    HOST="${SMOKE_HOST:-localhost}"
    PORT="${SMOKE_PORT:-8000}"
    URL="http://${HOST}:${PORT}/health"

    # Attempt up to 10 retries with 1s delay (server may still be starting)
    MAX_RETRIES=10
    RETRY=0
    while [ "$RETRY" -lt "$MAX_RETRIES" ]; do
      RESPONSE=$(wget -qO- "$URL" 2>&1) && break
      RETRY=$((RETRY + 1))
      echo "Attempt $RETRY/$MAX_RETRIES -- waiting for server at $URL..."
      sleep 1
    done

    if [ "$RETRY" -eq "$MAX_RETRIES" ]; then
      echo "ERROR: Server at $URL did not respond after $MAX_RETRIES attempts."
      exit 1
    fi

    # Check that status is healthy
    STATUS=$(echo "$RESPONSE" | grep -o '"status":"healthy"' || true)
    if [ -z "$STATUS" ]; then
      echo "ERROR: /health response did not contain expected status. Got:"
      echo "$RESPONSE"
      exit 1
    fi

    echo "OK: Server is healthy. Response: $RESPONSE"
    exit 0
    ;;
  *)
    echo "ERROR: Unknown command '$COMMAND'. Supported commands: serve, smoke"
    exit 1
    ;;
esac
