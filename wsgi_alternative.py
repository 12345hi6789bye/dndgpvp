# Alternative WSGI configuration for PythonAnywhere
# Use this if the main one doesn't work

import sys
import os

# add your project directory to the sys.path
project_home = '/home/12345hi6789bye/dndgpvp'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import the components
from flask import Flask
from flask_socketio import SocketIO

# Import the main app components
from app_production import app

# Create a new SocketIO instance configured specifically for WSGI
socketio_wsgi = SocketIO()

# Initialize with WSGI-compatible settings
socketio_wsgi.init_app(app,
                      async_mode='threading',
                      transports=['polling'],           # Polling only
                      cors_allowed_origins="*",
                      engineio_logger=False,
                      socketio_logger=False,
                      allow_upgrades=False,            # No WebSocket upgrades
                      ping_timeout=60,                 # Longer timeout for stability
                      ping_interval=25)

# The WSGI application
application = socketio_wsgi
