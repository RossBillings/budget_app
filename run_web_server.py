#!/usr/bin/env python3
"""
Simple script to run the Budget App web server.

Usage:
    python run_web_server.py
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from budget_app.web.server import main

if __name__ == '__main__':
    main()
