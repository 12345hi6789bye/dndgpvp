# PythonAnywhere Deployment Instructions

## Step-by-Step Setup:

### 1. Upload Files
- Upload all your project files to PythonAnywhere
- Make sure they're in a folder like `/home/yourusername/dndgpvp/`

### 2. Install Dependencies
Open a Bash console and run:
```bash
cd ~/dndgpvp
pip3.10 install --user -r requirements.txt
```

### 3. Configure Web App
1. Go to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration" (NOT Flask!)
4. Select Python 3.10

### 4. Set Working Directory
- In the Web tab, set "Working directory" to: `/home/yourusername/dndgpvp`

### 5. Configure WSGI File
1. Click on the WSGI configuration file link
2. **Delete all existing content**
3. **Copy and paste the ENTIRE contents** of `pythonanywhere_wsgi.py`
4. **Update the path**: Change `/home/12345hi6789bye/dndgpvp` to `/home/YOURUSERNAME/dndgpvp`
5. Save the file

### 6. Reload Web App
- Click the green "Reload" button
- Wait for it to finish reloading

### 7. Test Your App
- Visit your PythonAnywhere URL: `http://yourusername.pythonanywhere.com`
- You should see the login page

## If You Get Errors:

### WebSocket Errors:
- This is normal on PythonAnywhere
- The app automatically falls back to polling
- No action needed if the app still works

### Import Errors:
```bash
cd ~/dndgpvp
python3.10 test_wsgi.py
```
This will show you what's wrong.

### Still Not Working?
1. Try using `wsgi_alternative.py` contents instead
2. Check the error logs in the Web tab
3. Make sure all file paths are correct
4. Verify requirements.txt was installed successfully

## Your WSGI File Should Look Like This:
```python
import sys

project_home = '/home/YOURUSERNAME/dndgpvp'  # ← Update this path!
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from app_production import app, socketio

socketio.init_app(app, 
                 async_mode='threading',
                 transports=['polling'],
                 cors_allowed_origins="*",
                 engineio_logger=False,
                 socketio_logger=False,
                 allow_upgrades=False)

application = socketio
```

## That's It!
Your DNDG PVP Blackjack game should now be running on PythonAnywhere! 🎮
