#!/bin/bash

# Force script to target the root directory where this file actually sits
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Warn if local AI server isn't running
if ! pgrep -x "ollama" > /dev/null
then
    echo "⚠️ Warning: Ollama server does not appear to be running."
    echo "Make sure to run 'ollama run llama3' in another terminal window first!"
    echo "---------------------------------------------------------"
fi

# Activate local environment and launch the engine safely
source venv/bin/activate
python3 brain_engine.py
