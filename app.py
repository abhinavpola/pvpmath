import string
import random
from typing import Dict, List
from datetime import datetime, timedelta
from flask import Flask, render_template, request, Response, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit

from util import problem_generator
from names_generator import generate_name
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask_login import login_required, LoginManager, logout_user, login_user, UserMixin, current_user

load_dotenv()
cred = credentials.Certificate("pvpmath-firebase-adminsdk-k1jtt-0aae5478cf.json")
default_app = firebase_admin.initialize_app(cred)


app = Flask(__name__)
app.secret_key = "2c93e85111a3af498188d4ab376234f1bc65cd99fd8ea05db206b6252e158f8a"
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)


# Store active game rooms and their players
active_rooms = {}

# To tell which room a player is currently in (only 1 at a time)
player_rooms: Dict[str, str] = {}

# Scores for each player in each active room
scores: Dict[str, Dict[str, List[int]]] = {}

# Human-readable aliases for socket ids
aliases: Dict[str, str] = {}

db = firestore.client()

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

def firebase_authenticate(id_token):
    try:
        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        # Optionally, you can use the 'uid' to load user information from your database
        user = User()
        user.id = uid
        return user
    except auth.ExpiredIdTokenError:
        return None
    except auth.InvalidIdTokenError:
        return None


def save_score(score, duration):
    # Save the score in the 'all_scores' collection
    scores_ref = db.collection('all_scores').add({
        'score': score,
        'duration': duration
    })

def calculate_percentile(score, duration):
    query = db.collection('all_scores').where('duration', '==', duration)
    scores = [doc.to_dict()['score'] for doc in query.stream()]

    sorted_scores = sorted(scores)

    total_scores = len(sorted_scores)
    lower_count = sum(1 for s in sorted_scores if s <= score[0])

    percentile = (lower_count / total_scores) * 100

    return percentile

@app.route("/")
def index() -> Response:
    return render_template("index.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    response = Response("")
    response.headers["HX-Redirect"] = "/"
    return response

@app.route("/login", methods=["POST"])
def login() -> Response:
    id_token = request.json['idToken']
    user = firebase_authenticate(id_token)
    if user:
        logged_in = login_user(user)
        return Response(f"{logged_in}")
    else:
        return jsonify({'error': 'Invalid user ID token'})

@app.route("/battles")
@login_required
def battle_room() -> Response:
    args = request.args
    return render_template(
        "battle.html",
        room_code=args.get("roomcode"),
        player_name=args.get("playername"),
    )

@app.route("/home")
@login_required
def home_page() -> Response:
    return render_template(
            "home.html", player_name=generate_name(style="capital"), room_code=request.args.get("roomcode", default=""))    


@app.route("/start", methods=["POST"])
@login_required
def start_game() -> Response:
        room_code = generate_room_code()
        active_rooms[room_code] = {"time_limit": int(request.form.get("gameDuration")), "player_limit": int(request.form.get("numPlayers")), "players": set()}
        print(f"Room '{room_code}' created and waiting for {request.form.get('numPlayers')} players.")
        response = f"""
        <input type="text" class="form-control" id="challengeCode" name="challengeCode" value="{room_code}">
        """
        return response


@app.route("/join", methods=["POST"])
@login_required
def join_game() -> Response:
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


@socketio.on("disconnect")
def handle_disconnect():
    leave_player(request.sid)

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

@socketio.on("client_time_ended")
def time_ended(data: dict) -> None:
    room_code = data["room_code"]
    duration = active_rooms[room_code]["time_limit"]
    print(f"Time ended in room {room_code}")
    if datetime.now() > active_rooms[room_code]["end_time"]:
        print(f"Returning scores and percentiles for room: {room_code}")
        for score in scores[room_code].values():
            save_score(score[0], duration)
        for player, score in scores[room_code].items():
            scores[room_code][player][1] = calculate_percentile(score, duration)
        socketio.emit(
            "server_game_ended",
            {"scores": scores[room_code]},
            to=room_code,
        )
        print(f"Time's up in room '{room_code}'.")
        return
    else:
        print(f"Failed to correctly end game for room {room_code}")

@socketio.on("client_submitted_answer")
def check_answer(data: dict) -> None:
    room_code = data["room_code"]
    if datetime.now() > active_rooms[room_code]["end_time"]:
        socketio.emit(
            "server_game_ended",
            {"scores": scores[room_code]},
            to=room_code,
        )
        print(f"Time's up in room '{room_code}'.")
        return

    current_score = scores[room_code][aliases[request.sid]][0]

    if data["answer"] == active_rooms[room_code]["problems"][current_score]["answer"]:
        scores[room_code][aliases[request.sid]][0] += 1
        new_score = scores[room_code][aliases[request.sid]][0]
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
    active_rooms[room_code]["end_time"] = datetime.now() + timedelta(seconds=active_rooms[room_code]["time_limit"])

    # Send first problem before starting timer
    emit(
        "server_generated_problem",
        {"problem": active_rooms[room_code]["problems"][0]["problem"], "score": 0},
        to=room_code,
    )

    scores[room_code] = {}
    for player in active_rooms[room_code]["players"]:
        scores[room_code][player] = [0, None]

    emit("server_start_timer", {"time_limit": active_rooms[room_code]["time_limit"]}, to=room_code)


def generate_room_code() -> str:
    characters = string.ascii_uppercase + string.digits
    room_code = "".join(random.choice(characters) for _ in range(6))
    return room_code


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
