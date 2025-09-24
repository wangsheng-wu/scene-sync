#!/usr/bin/env python3
"""
Scene Sync - Photo Matching Application
Main entry point for both CLI and web interfaces
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.cli.commands import cli
from app.web.routes import create_app


def main():
    """Main entry point for the application"""
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Start web interface
        app = create_app()
        print("Starting Scene Sync web server...")
        print("Open http://localhost:5001 in your browser")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
    else:
        # Start CLI interface
        cli()


if __name__ == '__main__':
    main() 