# Deployment Guide

## For PythonAnywhere:

1. Upload all files to your PythonAnywhere account
2. Install dependencies in a Bash console:
   ```bash
   cd ~/dndgpvp
   pip3.10 install --user -r requirements.txt
   ```
3. In the Web tab, set up your web app:
   - Framework: Manual configuration (not Flask)
   - Python version: 3.10
4. Edit the WSGI configuration file and replace its contents with the contents of `pythonanywhere_wsgi.py`
5. Set the working directory to `/home/yourusername/dndgpvp`
6. Reload your web app

### If you get WebSocket errors:
- Try using `wsgi_alternative.py` contents instead
- Make sure all imports work in the PythonAnywhere console first

## For other WSGI servers:

1. Upload all files to your server
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Use the `wsgi.py` file:
   ```bash
   gunicorn --worker-class eventlet wsgi:application --bind 0.0.0.0:8080
   ```

## For servers with WebSocket support:

1. Use `app_production.py` directly:
   ```bash
   python app_production.py
   ```

## Environment Variables (optional):
- `FLASK_ENV=production` - Set to production mode
- `SECRET_KEY` - Override the default secret key

## Features:
- Automatic fallback from WebSocket to polling
- Threading async mode for WSGI compatibility  
- Error logging disabled in production
- CORS enabled for cross-origin requests

## Troubleshooting:
If you see "Cannot obtain socket from WSGI environment" errors:
1. Make sure you're using the correct WSGI file
2. Check that all dependencies are installed
3. Try the alternative WSGI configuration
4. Verify that the transports are set to `['polling']` only
