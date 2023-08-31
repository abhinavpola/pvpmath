from string import ascii_uppercase, digits
from random import choice
from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
socketio = SocketIO(app)

# Store active game rooms and their players
active_rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/battles/<room_code>')
def battle_room(room_code):
    return render_template('battle.html', room_code=room_code)

@socketio.on('start_game')
def start_game():
    room_code = generate_room_code()
    active_rooms[room_code] = {'players': []}
    join_room(room_code)
    socketio.emit('game_started', {'room_code': room_code})
    print(f"Room '{room_code}' created and waiting for players.")

@socketio.on('join_game')
def join_game(data):
    room_code = data['room_code']
    join_room(room_code)
    active_rooms[room_code]['players'].append(request.sid)
    if len(active_rooms[room_code]['players']) == 2:
        socketio.emit('both_players_joined', {'room_code': room_code}, room=room_code)
        print(f"Room '{room_code}' now has 2 players. Game can start!")

def generate_room_code():
    characters = ascii_uppercase + digits
    room_code = ''.join(choice(characters) for _ in range(6))
    return room_code

if __name__ == '__main__':
    socketio.run(app, debug=True)
