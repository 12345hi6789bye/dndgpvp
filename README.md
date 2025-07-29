# DNDG PVP Blackjack

A real-time multiplayer blackjack game that works across different computers on the same WiFi network.

## Features

- 🎮 Real-time multiplayer blackjack
- 🌐 Works across different devices on the same WiFi
- 🔐 Simple login system with player names
- 📱 Responsive design for mobile and desktop
- 🎨 Modern, beautiful UI with glass morphism effects
- ⚡ Live updates using WebSocket technology

## How to Run

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python app.py
   ```

3. **Access the game**:
   - The server will display the IP address to use
   - Open your browser and go to the displayed address (e.g., `http://192.168.1.100:8080`)
   - Other players on the same WiFi can access the game using the same URL

## How to Play

1. **Login**: Enter your player name
2. **Join a Game**: Use the default room "room1" or create your own room name
3. **Wait for Player 2**: The game needs exactly 2 players
4. **Take Turns**: Players alternate between hitting and standing
5. **Win Conditions**:
   - Get as close to 21 as possible without going over
   - If you go over 21, you bust and lose
   - Player with the highest total (≤21) wins
   - Both players bust = tie

## Game Rules

- Standard blackjack rules apply
- Aces are worth 11 (or 1 if it prevents busting)
- Face cards (Jack, Queen, King) are worth 10
- Number cards are worth their face value
- Players take turns hitting or standing
- Game ends when both players stand or bust

## Technical Details

- **Backend**: Flask with Socket.IO for real-time communication
- **Frontend**: Vanilla JavaScript with WebSocket
- **Storage**: In-memory (resets when server restarts)
- **Network**: Accessible to any device on the same WiFi network

## Troubleshooting

- **Can't access from other devices**: Make sure all devices are on the same WiFi network and the firewall isn't blocking the connection
- **Game not updating**: Refresh the page or check the browser console for errors
- **Server won't start**: Make sure port 8080 is available (or change the port in app.py)

Enjoy playing DNDG PVP Blackjack! 🎉
