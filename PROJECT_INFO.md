n# DNDG PVP Blackjack - Project Structure

## 📁 Project Files

```
DNDG PVP/
├── app.py                 # Development server (with debug mode)
├── app_network.py         # Network-aware server (BEST for hotspots)
├── app_production.py      # Production server (stable)
├── requirements.txt       # Python dependencies
├── README.md             # Detailed documentation
├── start_server.sh       # Quick start script
├── demo.sh              # Demo with instructions
├── network_diagnostic.py # Network troubleshooting tool
├── test_connection.py    # Connection testing tool
├── generate_qr.py        # QR code generator for mobile access
├── game_qr.png          # Generated QR code image
└── templates/           # HTML templates
    ├── base.html        # Base template with styling
    ├── login.html       # Login page
    └── index.html       # Main game interface
```

## 🚀 How to Run

### Option 1: Network-Aware Server (RECOMMENDED for iPad hotspot)
```bash
python app_network.py
```

### Option 2: Production Server  
```bash
python app_production.py
```

### Option 3: Development Server  
```bash
python app.py
```

### Option 4: Quick Demo
```bash
./demo.sh
```

## 🎮 Game Features

✅ **Real-time Multiplayer**: Socket.IO for instant updates  
✅ **Cross-Device Play**: Works on same WiFi network  
✅ **Simple Login**: Just enter your name  
✅ **Room System**: Multiple game rooms supported  
✅ **Turn-Based Play**: Alternating player turns  
✅ **Standard Blackjack**: Proper card values and rules  
✅ **Auto Ace Handling**: Aces convert from 11 to 1 automatically  
✅ **Health System**: Players start with 50 HP, take damage based on score difference  
✅ **Damage Calculation**: Loser takes (winner_score - loser_score) damage  
✅ **Bust Penalty**: Busting = 0 score, maximum damage taken  
✅ **Game Over**: Game ends when a player reaches 0 HP  
✅ **Win Tracking**: Track wins, rounds, and damage per player  
✅ **Two Reset Types**: Next round (keep health) or full reset (restore health)  
✅ **Responsive UI**: Works on mobile and desktop  
✅ **Beautiful Design**: Modern glass morphism styling with health bars  

## ⚡ Health System Rules

### Starting Health: 50 HP per player

### Damage Calculation:
- **Winner Score > Loser Score**: Damage = Winner's Total - Loser's Total
- **Bust = 0 Score**: If you bust, your score becomes 0 (maximum damage)
- **Tie**: No damage dealt to either player

### Examples:
- Player A: 19, Player B: 16 → Player B takes 3 damage (19-16=3)
- Player A: 21, Player B: Bust → Player B takes 21 damage (21-0=21) 
- Player A: 18, Player B: 18 → No damage (tie)
- Both Bust → No damage (both have 0 score)

### Game End:
- **Round Win**: Player with higher score wins, loser takes damage
- **Game Over**: When any player reaches 0 HP, game ends
- **Victory**: Last player standing wins the entire game

### Reset Options:
- **Next Round**: Continue with current health totals
- **Full Reset**: Restore both players to 50 HP

## 🔧 Technical Stack

- **Backend**: Flask + Socket.IO
- **Frontend**: Vanilla JavaScript + WebSocket
- **Styling**: CSS3 with modern effects
- **Session Management**: Flask sessions
- **Real-time Communication**: WebSocket protocol

## 🌐 Network Access

The server automatically detects your local IP address and displays:
- Local access: `http://127.0.0.1:8080`
- Network access: `http://[YOUR_IP]:8080`

Other devices on your WiFi can connect using the network address.

## 📱 iPad Hotspot Connection

### Current Status: ✅ READY
**Server running on**: `http://172.20.10.4:3000`

### For iPad Connection:
1. **Direct URL**: Open Safari and go to `http://172.20.10.4:3000`
2. **QR Code**: Scan the generated QR code with iPad camera
3. **Connection Test**: Run `python test_connection.py` to verify

### Troubleshooting iPad Connection:
- **Can't connect?** → Turn off iPad firewall temporarily
- **Page won't load?** → Try Safari's private browsing mode
- **Still issues?** → Run `python network_diagnostic.py` for analysis
- **Alternative ports**: Change to 4000, 5000, or 9000 in `app_network.py`

### Tools Available:
- `python network_diagnostic.py` - Check network setup
- `python test_connection.py` - Test if iPad can connect
- `python generate_qr.py` - Create QR code for easy access

## 🎯 Game Flow

1. **Login** → Enter player name
2. **Join Room** → Enter room name (default: "room1")
3. **Wait** → Wait for second player
4. **Play** → Take turns hitting/standing  
5. **Win** → Closest to 21 wins
6. **Reset** → Start new game

## 📱 Multi-Device Testing

1. Start server on computer A
2. Note the network IP address shown
3. On computer B, open: `http://[COMPUTER_A_IP]:8080`
4. Both players join same room
5. Play!

## 🛠️ Customization

- **Change Port**: Edit port number in `app_production.py`
- **Modify Styling**: Edit CSS in `templates/base.html`
- **Add Features**: Extend the BlackjackGame class
- **Room Names**: Use any room name you want

## 🐛 Common Issues

**Port in use**: Change port in the Python file  
**Can't connect**: Check firewall settings  
**Game not updating**: Refresh browser page  
**Session issues**: Clear browser cookies  

Enjoy your DNDG PVP Blackjack game! 🎉
