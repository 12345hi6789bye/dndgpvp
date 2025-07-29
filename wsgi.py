#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
Use this for deployment on PythonAnywhere, Heroku, or other WSGI servers.
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the Flask-SocketIO app
from app_production import app, socketio

# For WSGI servers that don't support WebSocket, we need to configure polling-only
socketio.init_app(app, 
                 async_mode='threading',
                 transports=['polling'],  # Use polling only for WSGI compatibility
                 cors_allowed_origins="*",
                 engineio_logger=False,
                 socketio_logger=False)

# WSGI application
application = app

if __name__ == "__main__":
    # For local testing
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
