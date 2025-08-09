#!/usr/bin/env bash
set -euo pipefail

# 1. ensure python3 is available
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Please install Python 3 first."
  exit 1
fi

# 2. create venv if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# 3. activate and upgrade pip
# note: if you're on macOS and using zsh, change bash to zsh in the next line
source venv/bin/activate
pip install --upgrade pip

# 4. install dependencies
pip install pandas matplotlib prettytable

echo
echo "✔️  All dependencies installed into ./venv"
echo "   Activate with:  source venv/bin/activate"