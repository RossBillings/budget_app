#!/usr/bin/env python3
"""
Web server entry point for the Budget App.

This module provides a development server for the web-based GUI.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from budget_app.web.app import create_app
from budget_app.core.models import engine, Base

def main():
    """Main entry point for the web server."""
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create Flask app
    app = create_app()
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Budget App Web Server...")
    print(f"Server will be available at: http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Press Ctrl+C to stop the server")
    
    # Run the Flask app
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )

if __name__ == '__main__':
    main()
