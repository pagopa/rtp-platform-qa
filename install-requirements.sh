#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

if [ -z "${VIRTUAL_ENV:-}" ]; then
  if [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
  fi
fi

echo "Running installations via Makefile..."

make install

make install-dev || true

make install-functional || true
make install-bdd || true
make install-ux || true
make install-performance || true
make install-contract || true

echo "Installations completed."