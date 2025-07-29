#!/bin/bash

# DNDG PVP Blackjack - Demo Script

echo "🎮 DNDG PVP Blackjack - Demo Instructions"
echo "========================================"
echo ""
echo "🚀 Quick Start:"
echo "1. Run: python app_production.py"
echo "2. Open browser: http://127.0.0.1:8080"
echo "3. Login with your name"
echo "4. Join game room 'room1'"
echo "5. Open another browser tab/device and repeat steps 2-4 with different name"
echo "6. Play blackjack!"
echo ""
echo "🌐 For Multi-Device Play:"
echo "1. Note the 'Network access' IP shown when starting the server"
echo "2. Other devices on same WiFi use that IP"
echo "3. Example: http://192.168.1.100:8080"
echo ""
echo "🎯 Game Rules:"
echo "- Get as close to 21 as possible"
echo "- Don't go over 21 (bust)"
echo "- Aces = 11 (or 1 to avoid busting)"
echo "- Face cards = 10"
echo "- Players alternate turns"
echo "- Reset game anytime"
echo ""
echo "🔧 Troubleshooting:"
echo "- Port busy? Change port in app_production.py"
echo "- Can't connect? Check firewall settings"
echo "- Game stuck? Refresh browser"
echo ""
echo "Press any key to continue..."
read -n 1 -s
echo ""
echo "Starting server..."
echo ""

# Navigate to the script directory
cd "$(dirname "$0")"

# Run the production app
source .venv/bin/activate
python app_production.py


# hes