#!/usr/bin/env python3
"""
Test script to verify WSGI configuration works correctly.
Run this on PythonAnywhere to test before deploying.
"""

try:
    print("Testing imports...")
    
    # Test basic imports
    from flask import Flask
    print("✅ Flask import successful")
    
    from flask_socketio import SocketIO
    print("✅ Flask-SocketIO import successful")
    
    # Test app import
    from app_production import app, socketio
    print("✅ Production app import successful")
    
    # Test WSGI configuration
    print("\nTesting WSGI configuration...")
    
    # Test the main WSGI file
    try:
        import pythonanywhere_wsgi
        print("✅ Main WSGI configuration loads successfully")
        print(f"   Application type: {type(pythonanywhere_wsgi.application)}")
    except Exception as e:
        print(f"❌ Main WSGI configuration failed: {e}")
        
        # Try alternative
        try:
            import wsgi_alternative
            print("✅ Alternative WSGI configuration loads successfully")
            print(f"   Application type: {type(wsgi_alternative.application)}")
        except Exception as e2:
            print(f"❌ Alternative WSGI configuration also failed: {e2}")
    
    # Test basic app functionality
    print("\nTesting app functionality...")
    with app.test_client() as client:
        # Test login page
        response = client.get('/login')
        if response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page failed: {response.status_code}")
    
    print("\n🎉 All tests passed! Your app should work on PythonAnywhere.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you've installed all requirements:")
    print("pip3.10 install --user -r requirements.txt")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("Check your app configuration and file paths.")
