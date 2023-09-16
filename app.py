import string
import random
import time
from typing import Dict, List

from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, join_room, leave_room, emit

PLAYER_LIMIT = 2

app = Flask(__name__)
socketio = SocketIO(app)

# Store active game rooms and their players
active_rooms: Dict[str, Dict[str, List[str]]] = {}

@app.route('/')
def index() -> Response:
    return render_template('index.html')

@app.route('/battles/<room_code>')
def battle_room(room_code: str) -> Response:
    args = request.args
    return render_template('battle.html', room_code=room_code, old_socket_id=args.get("old_socket_id"))

@socketio.on('client_start_game')
def start_game() -> None:
    room_code = generate_room_code()
    active_rooms[room_code] = {'players': []}
    emit('server_room_created', {'room_code': room_code})
    print(f"Room '{room_code}' created and waiting for players.")

@socketio.on('client_join_game')
def join_game(data: dict) -> None:
    room_code = data['room_code']
    if is_valid_room(room_code):
        join_player(room_code, request.sid)
        if is_room_full(room_code):
            emit('server_both_players_joined', {'room_code': room_code}, to=room_code)
            start_game_timer(room_code)
            print(f"Room '{room_code}' now has {PLAYER_LIMIT} players. Starting the timer...")
        else:
            emit('server_waiting_for_next_player', to=room_code)
    else:
        emit('server_invalid_room', {'message': 'Invalid room code or room is full'}, to=room_code)

@socketio.on('client_battle_load')
def update_socket_id(data: dict) -> None:
    if data['old_socket_id'] in active_rooms[data['room_code']]['players']:
        print(f"Found old socket {data['old_socket_id']} in room {data['room_code']}")     
        join_player(data['room_code'], request.sid)
        leave_player(data['room_code'], data['old_socket_id'])

def is_valid_room(room_code: str) -> bool:
    return room_code in active_rooms

def is_room_full(room_code: str) -> bool:
    return len(active_rooms[room_code]['players']) == PLAYER_LIMIT

def join_player(room_code: str, player_id: str) -> None:
    active_rooms[room_code]['players'].append(player_id)
    join_room(room_code, player_id)

def leave_player(room_code: str, player_id: str) -> None:
    active_rooms[room_code]['players'].remove(player_id)
    leave_room(room_code, player_id)

def start_game_timer(room_code: str) -> None:
    timer = 60
    while timer > 0:
        emit('server_timer_update', {'time': timer}, to=room_code)
        timer -= 1
        time.sleep(1)
    print(f"Time's up in room '{room_code}'.")

def generate_room_code() -> str:
    characters = string.ascii_uppercase + string.digits
    room_code = ''.join(random.choice(characters) for _ in range(6))
    return room_code

if __name__ == '__main__':
    socketio.run(app, debug=True)
