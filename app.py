import string
import random
import time
from typing import Dict, List

from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, join_room, leave_room, emit

from util import problem_generator
from names_generator import generate_name

PLAYER_LIMIT = 2
TIME_LIMIT_SECS = 60

app = Flask(__name__)
socketio = SocketIO(app)

RoomMap = Dict[str, Dict[str, List[str]]]

# Rooms on the home page
waiting_rooms: RoomMap = {}

# Store active game rooms and their players on the battle page
active_rooms: RoomMap = {}

# Scores for each player in each active room
scores: Dict[str, Dict[str, int]] = {}

# Human-readable aliases for socket ids
aliases: Dict[str, str] = {}


@app.route("/")
def index() -> Response:
    return render_template("index.html")


@app.route("/battles/<room_code>")
def battle_room(room_code: str) -> Response:
    args = request.args
    return render_template(
        "battle.html", room_code=room_code, old_socket_id=args.get("old_socket_id")
    )

@socketio.on("client_start_game")
def start_game() -> None:
    room_code = generate_room_code()
    waiting_rooms[room_code] = {"players": []}
    emit("server_room_created", {"room_code": room_code})
    print(f"Room '{room_code}' created and waiting for {PLAYER_LIMIT} players.")


@socketio.on("client_join_game")
def join_game(data: dict) -> None:
    room_code = data["room_code"]
    if room_code in waiting_rooms:
        join_player(room_code, request.sid, waiting_rooms)
        if is_room_full(room_code, waiting_rooms):
            emit("server_both_players_joined", {"room_code": room_code}, to=room_code)
            active_rooms[room_code] = {"players": []}
        else:
            emit("server_waiting_for_next_player", to=room_code)
    else:
        emit(
            "server_invalid_room",
            {"message": "Invalid room code or room is full"},
            to=room_code,
        )


@socketio.on("client_battle_load")
def update_socket_id(data: dict) -> None:
    room_code = data["room_code"]
    if data["old_socket_id"] in waiting_rooms[room_code]["players"]:
        print(f"Found old socket {data['old_socket_id']} in room {room_code}")
        join_player(room_code, request.sid, active_rooms)
        leave_player(room_code, data["old_socket_id"], waiting_rooms)
        aliases[request.sid] = generate_name(style="capital")

        # Send a nickname back to the requester
        emit("server_update_name", {"alias": f"alias: {aliases[request.sid]}"})

    if is_room_full(room_code, active_rooms):
        setup_problem_generator(room_code)
        start_game_timer(room_code)
        print(
            f"Room '{room_code}' now has {PLAYER_LIMIT} players. Starting the timer..."
        )


@socketio.on("client_submitted_answer")
def check_answer(data: dict) -> None:
    room_code = data["room_code"]
    current_score = scores[room_code][request.sid]

    if data["answer"] == active_rooms[room_code]["problems"][current_score]["answer"]:
        scores[room_code][request.sid] += 1
        new_score = scores[room_code][request.sid]
        emit(
            "server_generated_problem",
            {
                "problem": active_rooms[room_code]["problems"][new_score]["problem"],
                "score": new_score,
            },
            to=room_code,
        )


def is_room_full(room_code: str, room_map: RoomMap) -> bool:
    return len(room_map[room_code]["players"]) == PLAYER_LIMIT


def join_player(room_code: str, player_id: str, room_map: RoomMap) -> None:
    room_map[room_code]["players"].append(player_id)
    join_room(room_code, player_id)


def leave_player(room_code: str, player_id: str, room_map: RoomMap) -> None:
    room_map[room_code]["players"].remove(player_id)
    leave_room(room_code, player_id)


def setup_problem_generator(room_code):
    active_rooms[room_code]["problems"] = list(
        problem_generator.generate_arithmetic_problems(250, room_code)
    )


def start_game_timer(room_code: str) -> None:
    timer = TIME_LIMIT_SECS

    # Send first problem before starting timer
    emit(
        "server_generated_problem",
        {"problem": active_rooms[room_code]["problems"][0]["problem"], "score": 0},
        to=room_code,
    )

    scores[room_code] = {}
    for player in active_rooms[room_code]["players"]:
        scores[room_code][player] = 0

    def timer_task():
        nonlocal timer
        while timer > 0:
            socketio.emit("server_timer_update", {"time": timer}, to=room_code)
            timer -= 1
            time.sleep(1)
        socketio.emit(
            "server_game_ended",
            {"scores": {aliases[k]: v} for k, v in scores[room_code].items()},
            to=room_code,
        )
        print(f"Time's up in room '{room_code}'.")

    socketio.start_background_task(target=timer_task)


def generate_room_code() -> str:
    characters = string.ascii_uppercase + string.digits
    room_code = "".join(random.choice(characters) for _ in range(6))
    return room_code


if __name__ == "__main__":
    socketio.run(app, debug=True)
