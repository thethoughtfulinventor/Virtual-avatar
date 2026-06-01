#!/bin/bash

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "================================="
echo " Companion Engine V2"
echo "================================="

# Activate virtual environment if present
if [ -d "$ROOT_DIR/venv" ]; then
    source "$ROOT_DIR/venv/bin/activate"
fi

# Ensure required folders exist
mkdir -p "$ROOT_DIR/data"
mkdir -p "$ROOT_DIR/data/logs"

# Start the engine
python3 "$ROOT_DIR/main.py"
