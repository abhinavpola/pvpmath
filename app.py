import string
import random
import time
from typing import Dict, Any

from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_recaptcha import flask_recaptcha

from util import problem_generator
from names_generator import generate_name

import jsonpickle  # pip install jsonpickle
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins=["https://pvpmath.abhinavpola.com"])

app.config.update(dict(
    RECAPTCHA_ENABLED = True,
    RECAPTCHA_SITE_KEY = "6Ld8qxopAAAAAMEzo6uk2Af4Br38vUaFQR2fGISY",
    RECAPTCHA_SECRET_KEY = "6Ld8qxopAAAAAGHjN3NLivX7qnPGEBfREXXhu4TK",
))

recaptcha = flask_recaptcha.ReCaptcha()
recaptcha.init_app(app)

RoomMap = Dict[str, Dict[str, Any]]

# Store active game rooms and their players
active_rooms: RoomMap = {}

# To tell which room a player is currently in (only 1 at a time)
player_rooms: Dict[str, str] = {}

# Scores for each player in each active room
scores: Dict[str, Dict[str, int]] = {}

# Human-readable aliases for socket ids
aliases: Dict[str, str] = {}


@app.route("/")
def index() -> Response:
    return render_template("index.html", player_name=generate_name(style="capital"))


@app.route("/start", methods=["POST"])
def start_game() -> Response:
    if recaptcha.verify():
        room_code = generate_room_code()
        active_rooms[room_code] = {"players": set()}
        active_rooms[room_code]["player_limit"] = request.form.get("numPlayers")
        active_rooms[room_code]["time_limit"] = request.form.get("gameDuration")
        print(f"Room '{room_code}' created and waiting for {request.form.get('numPlayers')} players.")
        response = f"""
        <input type="text" class="form-control" id="challengeCode" name="challengeCode" value="{room_code}">
        """
        return response


@app.route("/join", methods=["POST"])
def join_game() -> Response:
    if recaptcha.verify():
        room_code = request.form.get("challengeCode")
        player_name = request.form.get("playerName")
        if room_code not in active_rooms:
            return '<div id="waitingSpinner">The game you are attempting to join doesn\'t exist...</div>'
        if player_name not in player_rooms:
            if not is_room_full(room_code):
                player_rooms[player_name] = room_code
                active_rooms[room_code]["players"].add(player_name)
            else:
                return '<div id="waitingSpinner">The game you are attempting to join is full...</div>'
        else:
            old_room_code = player_rooms[player_name]
            active_rooms[old_room_code]["players"].remove(player_name)
            if not is_room_full(room_code):
                player_rooms[player_name] = room_code
                active_rooms[room_code]["players"].add(player_name)
            else:
                return '<div id="waitingSpinner">The game you are attempting to join is full...</div>'

        if is_room_full(room_code):  # redirect
            response = Response("")
            response.headers[
                "HX-Redirect"
            ] = f"/battles?roomcode={room_code}&playername={player_name}"
            return response
        else:
            return f'<div id="waitingSpinner" hx-post="/join" hx-trigger="load delay:2s" hx-swap="outerHTML">You will be redirected once {active_rooms[room_code]["player_limit"] - len(active_rooms[room_code]["players"])} players have joined...</div>'


@app.route("/battles")
def battle_room() -> Response:
    args = request.args
    return render_template(
        "battle.html",
        room_code=args.get("roomcode"),
        player_name=args.get("playername"),
    )


@socketio.on("disconnect")
def handle_disconnect():
    print("player disconnecting")
    leave_player(request.sid)
    serialized = jsonpickle.encode(
        [
            active_rooms,
            player_rooms,
        ]
    )
    print(json.dumps(json.loads(serialized), indent=2))


@socketio.on("client_battle_load")
def assign_socket_id(data: dict) -> None:
    room_code = data["room_code"]
    player_name = data["player_name"]
    if player_name in active_rooms[room_code]["players"]:
        print(f"Found player {player_name} in room {room_code}")
        join_room(room_code, request.sid)
        aliases[request.sid] = player_name

    if is_room_full(room_code):
        setup_problem_generator(room_code)
        start_game_timer(room_code)
        print(
            f"Room '{room_code}' now has {active_rooms[room_code]['player_limit']} players. Starting the timer..."
        )


@socketio.on("client_submitted_answer")
def check_answer(data: dict) -> None:
    room_code = data["room_code"]
    current_score = scores[room_code][aliases[request.sid]]

    if data["answer"] == active_rooms[room_code]["problems"][current_score]["answer"]:
        scores[room_code][aliases[request.sid]] += 1
        new_score = scores[room_code][aliases[request.sid]]
        emit(
            "server_generated_problem",
            {
                "problem": active_rooms[room_code]["problems"][new_score]["problem"],
                "score": new_score,
            },
            to=request.sid,
        )


def is_room_full(room_code: str) -> bool:
    return len(active_rooms[room_code]["players"]) == active_rooms[room_code]["player_limit"]


def leave_player(player_id: str) -> None:
    if player_id in aliases and aliases[player_id] in player_rooms:
        room_code = player_rooms[aliases[player_id]]
        active_rooms[room_code]["players"].discard(aliases[player_id])
        del player_rooms[aliases[player_id]]
        if len(active_rooms[room_code]["players"]) == 0:
            _ = scores.pop(room_code, None)
            del active_rooms[room_code]
        del aliases[player_id]
        leave_room(room_code, player_id)


def setup_problem_generator(room_code):
    active_rooms[room_code]["problems"] = list(
        problem_generator.generate_arithmetic_problems(250, room_code)
    )


def start_game_timer(room_code: str) -> None:
    timer = active_rooms[room_code]["time_limit"]

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
            {"scores": scores[room_code]},
            to=room_code,
        )
        print(f"Time's up in room '{room_code}'.")

    socketio.start_background_task(target=timer_task)


def generate_room_code() -> str:
    characters = string.ascii_uppercase + string.digits
    room_code = "".join(random.choice(characters) for _ in range(6))
    return room_code


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
