#!/usr/bin/env bash
# Quick health check for Arajim backend.
set -e
PORT="${1:-8000}"
curl -sS "http://localhost:${PORT}/api/system/health" | python3 -m json.tool
