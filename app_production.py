from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dndg-blackjack-secret-key'
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading',
                   transports=['polling', 'websocket'],
                   engineio_logger=False,
                   socketio_logger=False)

# Game state storage
games = {}
players = {}

# Admin password for protected actions
ADMIN_PASSWORD = "42376-EGRdfhbj-134fhud"

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
    
    def add_player(self, player_id, player_name, as_spectator=False):
        if as_spectator:
            # Add as spectator (no limit on spectators)
            if 'spectators' not in self.__dict__:
                self.spectators = {}
            self.spectators[player_id] = {
                "name": player_name,
                "is_spectator": True
            }
            return True
        elif len(self.players) < 2:
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
        # Check if player is a spectator first
        if hasattr(self, 'spectators') and player_id in self.spectators:
            del self.spectators[player_id]
            return
            
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
        
        # 5-card trick: if player has 5 cards without busting, treat as 21
        if len(hand) == 5 and total <= 21:
            return 21
            
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
            elif len(self.players[player_id]["hand"]) == 5:
                # 5-card trick achieved - automatically stand
                self.players[player_id]["status"] = "stood"
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
            
            # Schedule auto-next round after 2 seconds (unless someone died)
            if self.game_state != "game_over":
                import threading
                def auto_next_round():
                    import time
                    time.sleep(2)
                    if self.game_state == "finished":  # Only proceed if still finished
                        self.reset_game()
                        socketio.emit('game_update', self.get_game_state(), room=self.game_id)
                        socketio.emit('game_reset', {
                            'message': 'Auto-advancing to next round...'
                        }, room=self.game_id)
                
                thread = threading.Thread(target=auto_next_round)
                thread.daemon = True
                thread.start()
    
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
    
    def admin_give_card(self, target_player_id, card_name):
        """Admin function to give a specific card to a player"""
        if (target_player_id in self.players and 
            self.players[target_player_id]["status"] == "playing"):
            
            # Find the card in the deck
            card_to_give = None
            for i, card in enumerate(self.deck):
                if card["name"].lower() == card_name.lower():
                    card_to_give = self.deck.pop(i)
                    break
            
            if card_to_give:
                self.players[target_player_id]["hand"].append(card_to_give)
                self.players[target_player_id]["total"] = self.calculate_total(self.players[target_player_id]["hand"])
                
                if self.players[target_player_id]["total"] > 21:
                    self.players[target_player_id]["status"] = "bust"
                elif len(self.players[target_player_id]["hand"]) == 5:
                    self.players[target_player_id]["status"] = "stood"
                
                self.check_game_end()
                return card_to_give
        return None
    
    def get_game_state(self):
        spectators = getattr(self, 'spectators', {})
        return {
            "game_id": self.game_id,
            "players": self.players,
            "spectators": spectators,
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
            "current_health": {
                player_ids[0]: self.players[player_ids[0]].get("health", 50),
                player_ids[1]: self.players[player_ids[1]].get("health", 50)
            }
        }

@app.route('/')
def index():
    if 'player_name' not in session or 'player_id' not in session:
        return redirect(url_for('login'))
    return render_template('lobby.html', player_name=session['player_name'])

@app.route('/<room_code>')
def room(room_code):
    if 'player_name' not in session or 'player_id' not in session:
        return redirect(url_for('login'))
    
    # Check if room exists and get player count
    room_exists = room_code in games
    player_count = len(games[room_code].players) if room_exists else 0
    can_join_as_player = player_count < 2
    
    return render_template('room.html', 
                         player_name=session['player_name'],
                         room_code=room_code,
                         room_exists=room_exists,
                         player_count=player_count,
                         can_join_as_player=can_join_as_player)

@app.route('/quickgame')
def quickgame():
    if 'player_name' not in session or 'player_id' not in session:
        return redirect(url_for('login'))
    return render_template('index_simple.html', player_name=session['player_name'])

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content response for favicon

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
    as_spectator = data.get('as_spectator', False)
    
    if game_id not in games:
        games[game_id] = BlackjackGame(game_id)
    
    game = games[game_id]
    
    if game.add_player(player_id, player_name, as_spectator):
        join_room(game_id)
        players[player_id]['game_id'] = game_id
        
        role = "spectator" if as_spectator else "player"
        emit('joined_game', {
            'game_id': game_id,
            'player_id': player_id,
            'role': role,
            'message': f'Joined game {game_id} as {role}'
        })
        
        socketio.emit('game_update', game.get_game_state(), room=game_id)
    else:
        emit('error', {'message': 'Game is full or error joining game'})

@socketio.on('leave_game')
def on_leave_game():
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    player_name = players[player_id]["name"]
    
    game.remove_player(player_id)
    leave_room(game_id)
    players[player_id]['game_id'] = None
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('player_action', {
        'message': f'{player_name} left the game'
    }, room=game_id)
    
    emit('left_game', {'message': 'You have left the game'})

@socketio.on('admin_give_card')
def on_admin_give_card(data):
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    # Check admin password
    password = data.get('password', '')
    if password != ADMIN_PASSWORD:
        emit('error', {'message': 'Invalid admin password'})
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    target_player_id = data.get('target_player_id')
    card_name = data.get('card_name')
    
    if target_player_id and card_name:
        card = game.admin_give_card(target_player_id, card_name)
        if card:
            target_name = game.players[target_player_id]["name"]
            socketio.emit('game_update', game.get_game_state(), room=game_id)
            socketio.emit('card_drawn', {
                'player_id': target_player_id,
                'card': card,
                'message': f'Admin gave {card["name"]} to {target_name}'
            }, room=game_id)
            emit('admin_success', {'message': f'Successfully gave {card["name"]} to {target_name}'})
        else:
            emit('error', {'message': 'Card not found or player cannot receive cards'})
    else:
        emit('error', {'message': 'Missing target player or card name'})

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
def on_reset_game(data=None):
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    # Check admin password
    password = data.get('password', '') if data else ''
    if password != ADMIN_PASSWORD:
        emit('error', {'message': 'Admin password required for manual reset'})
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    game.reset_game()
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('game_reset', {
        'message': f'Game reset by {players[player_id]["name"]} (Admin)'
    }, room=game_id)

@socketio.on('full_reset_game')
def on_full_reset_game(data=None):
    if 'player_id' not in session:
        return
    
    player_id = session['player_id']
    if player_id not in players:
        return
    
    # Check admin password
    password = data.get('password', '') if data else ''
    if password != ADMIN_PASSWORD:
        emit('error', {'message': 'Admin password required for full reset'})
        return
    
    game_id = players[player_id].get('game_id')
    if not game_id or game_id not in games:
        return
    
    game = games[game_id]
    game.reset_game(full_reset=True)
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('game_reset', {
        'message': f'Full game reset by {players[player_id]["name"]} (Admin) - All health and stats restored!'
    }, room=game_id)

@socketio.on('create_room')
def on_create_room():
    if 'player_id' not in session:
        return
    
    # Generate a unique room code
    import string
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    while room_code in games:  # Ensure uniqueness
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    games[room_code] = BlackjackGame(room_code)
    
    emit('room_created', {
        'room_code': room_code,
        'message': f'Room {room_code} created successfully!'
    })

@socketio.on('get_room_list')
def on_get_room_list():
    if 'player_id' not in session:
        return
    
    room_list = []
    for room_code, game in games.items():
        player_count = len(game.players)
        spectator_count = len(getattr(game, 'spectators', {}))
        room_list.append({
            'room_code': room_code,
            'player_count': player_count,
            'spectator_count': spectator_count,
            'game_state': game.game_state,
            'can_join': player_count < 2
        })
    
    emit('room_list', {'rooms': room_list})

@socketio.on('delete_room')
def on_delete_room(data):
    if 'player_id' not in session:
        return
    
    room_code = data.get('room_code')
    password = data.get('password', '')
    
    # Check admin password for room deletion
    if password != ADMIN_PASSWORD:
        emit('error', {'message': 'Invalid admin password for room deletion'})
        return
    
    if room_code and room_code in games:
        # Notify all players in the room
        socketio.emit('room_deleted', {
            'message': 'This room has been deleted by an administrator'
        }, room=room_code)
        
        # Remove all players from the room
        game = games[room_code]
        for player_id in list(game.players.keys()):
            if player_id in players:
                players[player_id]['game_id'] = None
        
        # Delete the room
        del games[room_code]
        
        emit('admin_success', {'message': f'Room {room_code} deleted successfully'})
    else:
        emit('error', {'message': 'Room not found'})

if __name__ == '__main__':
    # Get the local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"🎮 DNDG PVP Blackjack Server Starting...")
    print(f"📍 Local access: http://127.0.0.1:8080")
    print(f"🌐 Network access: http://{local_ip}:8080")
    print(f"🎯 Other devices on WiFi can connect to: http://{local_ip}:8080")
    print("")
    
    # Try to use eventlet for better WebSocket support
    try:
        import eventlet
        eventlet.monkey_patch()
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    except ImportError:
        # Fallback to threading mode if eventlet not available
        socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
#test 3