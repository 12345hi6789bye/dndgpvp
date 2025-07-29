from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dndg-blackjack-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state storage
games = {}
players = {}

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
                "status": "playing",  # playing, stood, bust
                "ready": False
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
    
    def start_game(self):
        if len(self.players) == 2:
            self.game_state = "playing"
            player_ids = list(self.players.keys())
            self.current_player = player_ids[0]
            # Reset all players
            for player_id in self.players:
                self.players[player_id]["hand"] = []
                self.players[player_id]["total"] = 0
                self.players[player_id]["status"] = "playing"
                self.players[player_id]["ready"] = True
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
        player_scores = {}
        for player_id, player in self.players.items():
            if player["status"] == "bust":
                player_scores[player_id] = 0
            else:
                player_scores[player_id] = player["total"]
        
        max_score = max(player_scores.values())
        if max_score == 0:
            self.winner = "tie"  # Both busted
        else:
            winners = [p_id for p_id, score in player_scores.items() if score == max_score]
            if len(winners) == 1:
                self.winner = winners[0]
            else:
                self.winner = "tie"
    
    def reset_game(self):
        self.deck = self.create_deck()
        self.game_state = "playing"
        self.winner = None
        player_ids = list(self.players.keys())
        if len(player_ids) >= 1:
            self.current_player = player_ids[0]
        
        for player_id in self.players:
            self.players[player_id]["hand"] = []
            self.players[player_id]["total"] = 0
            self.players[player_id]["status"] = "playing"
    
    def get_game_state(self):
        return {
            "game_id": self.game_id,
            "players": self.players,
            "current_player": self.current_player,
            "game_state": self.game_state,
            "winner": self.winner,
            "cards_left": len(self.deck)
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
    game.reset_game()
    
    socketio.emit('game_update', game.get_game_state(), room=game_id)
    socketio.emit('game_reset', {
        'message': f'Game reset by {players[player_id]["name"]}'
    }, room=game_id)

if __name__ == '__main__':
    # Get the local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"Starting server on http://{local_ip}:8080")
    print(f"Other devices on the same WiFi can access: http://{local_ip}:8080")
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)


# 3