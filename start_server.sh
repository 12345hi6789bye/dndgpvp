#!/bin/bash

# DNDG PVP Blackjack - Startup Script

echo "🎮 Starting DNDG PVP Blackjack Server..."
echo ""

# Navigate to the script directory
cd "$(dirname "$0")"

# Activate virtual environment and run the production app
source .venv/bin/activate
python app_production.py
