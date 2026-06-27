#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Setting up dependencies ==="

# --- Python venv setup ---
if [[ "$OSTYPE" == "darwin"* ]]; then
    VENV_DIR="$HOME/rag_venv_mac/venv"
else
    VENV_DIR="$HOME/rag_venv/venv"
fi

if [[ ! -f "$VENV_DIR/bin/pip" ]]; then
    echo "Creating Python virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Python venv already exists."
fi

echo "Installing/verifying Python packages..."
"$VENV_DIR/bin/pip" install --quiet \
    fastapi \
    uvicorn \
    "psycopg[binary]" \
    python-dotenv \
    FlagEmbedding \
    requests \
    google-genai \
    pyyaml \
    gitpython \
    numpy

echo "Python packages ready."

# --- Node/React setup ---
if ! command -v node > /dev/null 2>&1; then
    echo "ERROR: Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org and re-run this script."
    exit 1
fi

if ! command -v npm > /dev/null 2>&1; then
    echo "ERROR: npm is not installed."
    echo "Please install Node.js from https://nodejs.org and re-run this script."
    exit 1
fi

UI_DIR="$SCRIPT_DIR/debug-assistant-ui"

if [[ ! -d "$UI_DIR/node_modules" ]] || [[ ! -f "$UI_DIR/node_modules/.bin/react-scripts" ]]; then
    echo "Installing React dependencies..."
    cd "$UI_DIR" && npm install --silent
    cd "$SCRIPT_DIR"
    echo "React dependencies ready."
else
    echo "React dependencies already installed."
fi

echo "=== All dependencies ready ==="
