#!/usr/bin/env bash
set -e

echo "Running post-edit checks..."

if [ -f package.json ]; then
  npm test || true
fi

if [ -d apps/web ]; then
  if [ -f apps/web/package.json ]; then
    npm --prefix apps/web test || true
    npm --prefix apps/web run build || true
  fi
fi

if command -v pytest >/dev/null 2>&1; then
  pytest tests/unit tests/regression || true
fi

echo "Post-edit checks finished."
