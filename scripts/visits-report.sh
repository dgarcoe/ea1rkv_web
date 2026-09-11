#!/usr/bin/env bash
# Writes HTML to stdout. Build the goaccess image before running.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
compose=(docker compose -f docker-compose.prod.external.yml -f docker-compose.analytics.yml)
"${compose[@]}" logs --no-color --no-log-prefix nginx |
  "${compose[@]}" run --rm --no-deps -T goaccess
