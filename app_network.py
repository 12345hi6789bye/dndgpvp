from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import json
import os
from datetime import datetime
import uuid
import socket
import subprocess
import platform

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dndg-blackjack-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state storage
games = {}
players = {}

def get_network_ip():
    """Get the actual network IP address, including hotspot scenarios"""
    try:
        # Try to get IP from network interfaces
        if platform.system() == "Darwin":  # macOS
            try:
                # Try to get IP from route to 8.8.8.8
                result = subprocess.run(['route', 'get', '8.8.8.8'], 
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'interface:' in line:
                        interface = line.split(':')[1].strip()
                        # Get IP for this interface
                        ifconfig_result = subprocess.run(['ifconfig', interface], 
                                                       capture_output=True, text=True, timeout=5)
                        for ifconfig_line in ifconfig_result.stdout.split('\n'):
                            if 'inet ' in ifconfig_line and '127.0.0.1' not in ifconfig_line:
                                ip = ifconfig_line.split()[1]
                                return ip
            except:
                pass
        
        # Fallback 1: Connect to external server to determine local IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to Google DNS
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                if ip != "127.0.0.1":
                    return ip
        except:
            pass
        
        # Fallback 2: Get hostname IP
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip != "127.0.0.1":
                return ip
        except:
            pass
        
        # Fallback 3: Get all network interfaces
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            return ip
        except ImportError:
            pass
            
        return "127.0.0.1"
    except Exception as e:
        print(f"Error getting network IP: {e}")
        return "127.0.0.1"

def get_all_network_ips():
    """Get all possible network IPs for display"""
    ips = set()
    
    # Add the primary network IP
    primary_ip = get_network_ip()
    ips.add(primary_ip)
    
    try:
        # Get all network interfaces (manual approach for cross-platform)
        if platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=10)
                current_interface = None
                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t') and not line.startswith(' '):
                        current_interface = line.split(':')[0]
                    elif 'inet ' in line and '127.0.0.1' not in line:
                        ip = line.strip().split()[1]
                        if not ip.startswith('169.254.'):  # Skip link-local
                            ips.add(ip)
            except:
                pass
    except:
        pass
    
    return list(ips)

class BlackjackGame:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = {}
        self.deck = self.create_deck()
        self.current_player = None
        self.game_state = "waiting"  # waiting, playing, finished
        self.winner = None
        
    def create_deck(self):
        deck = []
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        for suit in suits:
            numbers = ['Ace'] + list(range(2, 11)) + ['Jack', 'Queen', 'King']
            for number in numbers:
                if number in ['Jack', 'Queen', 'King']:
                    value = 10
                elif number == 'Ace':
                    value = 11
                else:
                    value = number
                deck.append({
                    "name": f"{number} of {suit}",
                    "suit": suit,
                    "value": value,
                    "number": number
                })
        random.shuffle(deck)
        return deck
    
    def add_player(self, player_id, player_name):
        if len(self.players) < 2:
            self.players[player_id] = {
                "name": player_name,
                "hand": [],
                "total": 0,
                "health": 50,  # Starting health
                "status": "playing",  # playing, stood, bust
                "ready": False,
                "damage_taken": 0,  # Track damage taken this round
                "wins": 0,  # Track total wins
                "rounds_played": 0  # Track total rounds
            }
            if len(self.players) == 2:
                self.start_game()
            return True
        return False
    
    def remove_player(self, player_id):
        if player_id in self.players:
            del self.players[player_id]
            if len(self.players) == 0:
                self.game_state = "waiting"
            elif len(self.players) == 1:
                self.game_state = "waiting"
                # Reset the remaining player
                for p_id in self.players:
                    self.players[p_id]["hand"] = []
                    self.players[p_id]["total"] = 0
                    self.players[p_id]["status"] = "playing"
                    self.players[p_id]["ready"] = False
                    self.players[p_id]["damage_taken"] = 0
    
    def start_game(self):
        if len(self.players) == 2:
            self.game_state = "playing"
            player_ids = list(self.players.keys())
            self.current_player = player_ids[0]
            # Reset all players for new round
            for player_id in self.players:
                self.players[player_id]["hand"] = []
                self.players[player_id]["total"] = 0
                self.players[player_id]["status"] = "playing"
                self.players[player_id]["ready"] = True
                self.players[player_id]["damage_taken"] = 0
            self.deck = self.create_deck()
    
    def calculate_total(self, hand):
        total = sum(card['value'] for card in hand)
        aces = sum(1 for card in hand if card['number'] == 'Ace')
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    def hit(self, player_id):
        if (self.game_state == "playing" and 
            player_id in self.players and 
            self.current_player == player_id and
            self.players[player_id]["status"] == "playing" and
            len(self.deck) > 0):
            
            card = self.deck.pop()
            self.players[player_id]["hand"].append(card)
            self.players[player_id]["total"] = self.calculate_total(self.players[player_id]["hand"])
            
            if self.players[player_id]["total"] > 21:
                self.players[player_id]["status"] = "bust"
                self.switch_turn()
            else:
                self.switch_turn()
            
            self.check_game_end()
            return card
        return None
    
    def stand(self, player_id):
        if (self.game_state == "playing" and 
            player_id in self.players and 
            self.current_player == player_id and
            self.players[player_id]["status"] == "playing"):
            
            self.players[player_id]["status"] = "stood"
            self.switch_turn()
            self.check_game_end()
            return True
        return False
    
    def switch_turn(self):
        player_ids = list(self.players.keys())
        if len(player_ids) == 2:
            current_index = player_ids.index(self.current_player)
            next_index = (current_index + 1) % 2
            next_player = player_ids[next_index]
            
            # Only switch if the next player is still playing
            if self.players[next_player]["status"] == "playing":
                self.current_player = next_player
            else:
                # If next player is done, check if current player can still play
                if self.players[self.current_player]["status"] != "playing":
                    self.current_player = None
    
    def check_game_end(self):
        active_players = [p for p in self.players.values() if p["status"] == "playing"]
        if len(active_players) == 0:
            self.game_state = "finished"
            self.determine_winner()
    
    def determine_winner(self):
        """Determine winner and calculate damage based on score difference"""
        player_ids = list(self.players.keys())
        player_scores = {}
        
        # Calculate effective scores (0 if bust)
        for player_id, player in self.players.items():
            if player["status"] == "bust":
                player_scores[player_id] = 0
            else:
                player_scores[player_id] = player["total"]
        
        # Get the two players
        p1_id, p2_id = player_ids[0], player_ids[1]
        p1_score, p2_score = player_scores[p1_id], player_scores[p2_id]
        
        # Calculate damage based on score difference
        if p1_score == p2_score:
            # Tie - no damage
            self.winner = "tie"
            damage = 0
        elif p1_score > p2_score:
            # Player 1 wins
            self.winner = p1_id
            damage = p1_score - p2_score
            # Apply damage to player 2
            self.players[p2_id]["health"] = max(0, self.players[p2_id]["health"] - damage)
            self.players[p2_id]["damage_taken"] = damage
            self.players[p1_id]["damage_taken"] = 0
            self.players[p1_id]["wins"] += 1
        else:
            # Player 2 wins
            self.winner = p2_id
            damage = p2_score - p1_score
            # Apply damage to player 1
            self.players[p1_id]["health"] = max(0, self.players[p1_id]["health"] - damage)
            self.players[p1_id]["damage_taken"] = damage
            self.players[p2_id]["damage_taken"] = 0
            self.players[p2_id]["wins"] += 1
        
        # Update rounds played
        for player_id in self.players:
            self.players[player_id]["rounds_played"] += 1
        
        # Check if anyone died (health <= 0)
        dead_players = [pid for pid, player in self.players.items() if player["health"] <= 0]
        if dead_players:
            self.game_state = "game_over"
            # Winner is the surviving player
            alive_players = [pid for pid, player in self.players.items() if player["health"] > 0]
            if alive_players:
                self.winner = alive_players[0]
            else:
                self.winner = "double_death"  # Both died somehow
    
    def reset_game(self, full_reset=False):
        """Reset game - full_reset restarts health, otherwise just starts new round"""
        self.deck = self.create_deck()
        self.winner = None
        player_ids = list(self.players.keys())
        if len(player_ids) >= 1:
            self.current_player = player_ids[0]
        
        # Always reset round-specific data
        for player_id in self.players:
            self.players[player_id]["hand"] = []
            self.players[player_id]["total"] = 0
            self.players[player_id]["status"] = "playing"
            self.players[player_id]["damage_taken"] = 0
        
        # If full reset or someone died, reset health and stats
        if full_reset or self.game_state == "game_over":
            for player_id in self.players:
                self.players[player_id]["health"] = 50
                self.players[player_id]["wins"] = 0
                self.players[player_id]["rounds_played"] = 0
            self.game_state = "playing"
        else:
            # Just continue with next round if no one died
            self.game_state = "playing"
    
    def get_game_state(self):
        return {
            "game_id": self.game_id,
            "players": self.players,
            "current_player": self.current_player,
            "game_state": self.game_state,
            "winner": self.winner,
            "cards_left": len(self.deck),
            "round_info": self.get_round_info()
        }
    
    def get_round_info(self):
        """Get information about the current round and damage"""
        if not self.players:
            return {}
        
        player_ids = list(self.players.keys())
        if len(player_ids) < 2:
            return {}
        
        return {
            "damage_dealt": {
                player_ids[0]: self.players[player_ids[0]].get("damage_taken", 0),
                player_ids[1]: self.players[player_ids[1]].get("damage_taken", 0)
            },
            "is_game_over": self.game_state == "game_over",
            "health_status": {
                player_ids[0]: self.players[player_ids[0]].get("health", 50),
                player_ids[1]: self.players[player_ids[1]].get("health", 50)
            }
        }

@app.route('/')
def index():
    if 'player_name' not in session or 'player_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', player_name=session['player_name'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        player_name = request.form.get('player_name', '').strip()
        if player_name:
            session['player_name'] = player_name
            session['player_id'] = str(uuid.uuid4())
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Please enter a valid name")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@socketio.on('connect')
def on_connect():
    if 'player_name' not in session or 'player_id' not in session:
        return False
    
    player_id = session['player_id']
    player_name = session['player_name']
    players[player_id] = {
        "name": player_name,
        "session_id": request.sid,
        "game_id": None
    }
    
    print(f"Player {player_name} connected")
    emit('connected', {'message': f'Welcome, {player_name}!'})

@socketio.on('disconnect')
def on_disconnect():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id in players:
        game_id = players[player_id].get('game_id')
        if game_id and game_id in games:
            game = games[game_id]
            game.remove_player(player_id)
            socketio.emit('game_update', game.get_game_state(), room=game_id)
            
            # Clean up empty games
            if len(game.players) == 0:
                del games[game_id]
        
        del players[player_id]
    
    print(f"Player disconnected")

@socketio.on('join_game')
def on_join_game(data):
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    player_name = session['player_name']
    game_id = data.get('game_id', 'default')
    
    if game_id not in games:
        games[game_id] = BlackjackGame(game_id)
    
    game = games[game_id]
    
    if game.add_player(player_id, player_name):
        join_room(game_id)
        players[player_id]['game_id'] = game_id
        
        emit('joined_game', {
            'game_id': game_id,
            'player_id': player_id,
            'message': f'Joined game {game_id}'
        })
        
        socketio.emit('game_update', game.get_game_state(), room=game_id)
    else:
        emit('error', {'message': 'Game is full or error joining game'})

@socketio.on('hit')
def on_hit():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    card = game.hit(player_id)
    
    if card:
        socketio.emit('game_update', game.get_game_state(), room=game_id)
        socketio.emit('card_drawn', {
            'player_id': player_id,
            'card': card,
            'message': f'{players[player_id]["name"]} drew {card["name"]}'
        }, room=game_id)

@socketio.on('stand')
def on_stand():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    if game.stand(player_id):
        socketio.emit('game_update', game.get_game_state(), room=game_id)
        socketio.emit('player_action', {
            'player_id': player_id,
            'action': 'stand',
            'message': f'{players[player_id]["name"]} stands'
        }, room=game_id)

@socketio.on('reset_game')
def on_reset_game():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    game.reset_game(full_reset=False)  # Just new round by default
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('game_reset', {
        'message': f'New round started by {players[player_id]["name"]}'
    }, room=game_id)

@socketio.on('full_reset_game')
def on_full_reset_game():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    game.reset_game(full_reset=True)  # Full reset with health
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('game_reset', {
        'message': f'Game completely reset by {players[player_id]["name"]} - Health restored!'
    }, room=game_id)

if __name__ == '__main__':
    port = 3000  # Use available port from diagnostic
    
    print("🎮 DNDG PVP Blackjack Server Starting...")
    print("=" * 50)
    
    # Get all possible network IPs
    network_ips = get_all_network_ips()
    
    print(f"📍 Local access: http://127.0.0.1:{port}")
    print("")
    print("🌐 Network access options:")
    for ip in network_ips:
        if ip != "127.0.0.1":
            print(f"   • http://{ip}:{port}")
    print("")
    
    print("📱 For iPad hotspot connections:")
    print("   🎯 IMPORTANT: iPad should connect to:")
    for ip in network_ips:
        if ip.startswith("172.20.10.") and ip != "127.0.0.1":
            print(f"      → http://{ip}:{port}")
            print(f"   💡 The iPad (hotspot provider) should use this URL")
            break
    print("")
    
    print("🔧 Troubleshooting:")
    print("   • iPad can't connect? Turn off iPad's firewall temporarily")
    print("   • Still issues? Try Safari's private/incognito mode")
    print("   • Check that iPad and laptop are on same hotspot")
    print(f"   • Alternative ports: {port+1000}, {port+2000}")
    print("")
    
    print("Starting server...")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)


# commit test