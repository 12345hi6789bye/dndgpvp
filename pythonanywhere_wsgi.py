# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# Updated for Flask-SocketIO support

import sys

# add your project directory to the sys.path
project_home = '/home/12345hi6789bye/dndgpvp'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import Flask-SocketIO app properly configured for WSGI
from app_production import app, socketio

# Configure SocketIO for WSGI deployment (polling only for compatibility)
socketio.init_app(app, 
                 async_mode='threading',
                 transports=['polling'],  # Use polling only for WSGI compatibility
                 cors_allowed_origins="*",
                 engineio_logger=False,
                 socketio_logger=False,
                 allow_upgrades=False)    # Disable WebSocket upgrades

# WSGI application - use the SocketIO WSGI app, not the Flask app directly
application = socketio
