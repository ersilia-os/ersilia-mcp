#!/usr/bin/env bash
# Bring up the local Isaura store so the cache tools and the integration
# tests work without extra setup. Runs on every attach, so it must be
# idempotent and must not fail the attach.
set -uo pipefail

ENV_NAME="ersilia-mcp"

if curl -sf --max-time 5 http://127.0.0.1:9000/minio/health/live >/dev/null 2>&1; then
  echo "Isaura store already running."
  exit 0
fi

echo "Starting the Isaura store..."
if ! conda run --no-capture-output -n "${ENV_NAME}" isaura engine --start; then
  echo "Could not start the Isaura store. Start it by hand with:"
  echo "  isaura engine --start"
  exit 0
fi

# `isaura engine --start` exits 0 even when the containers fail to come up,
# so confirm the store actually answers before calling it ready.
for _ in $(seq 1 10); do
  if curl -sf --max-time 5 http://127.0.0.1:9000/minio/health/live >/dev/null 2>&1; then
    echo "Isaura store ready on port 9000 (console on 9001)."
    exit 0
  fi
  sleep 2
done

echo "Isaura store did not become reachable. Check 'isaura engine' for status."
exit 0
