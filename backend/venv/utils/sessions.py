# session.py
import uuid, time

sessions = {}

TOTAL_ROUNDS = 5

def create_session(player_name):
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "players": [
            {"id": str(uuid.uuid4()), "name": player_name, "code": "", "score": 0},
            {"id": None, "name": None, "code": "", "score": 0}
        ],
        "problem_id": 1,
        "round": 1,
        "roundsTotal": TOTAL_ROUNDS,
        "round_duration": 300,
        "roundEndsAt": None,
        "status": "active",     # "active" | "ended" | "completed"
        "winnerId": None,       # round winner
        "championId": None      # overall winner at the end of round 5
    }
    return session_id, sessions[session_id]

def join_session(session_id, player_name):
    session = sessions.get(session_id)
    if not session:
        return None
    for player in session["players"]:
        if player["name"] is None:
            player["name"] = player_name
            player["id"] = str(uuid.uuid4())
            if session.get("roundEndsAt") is None:
                session["roundEndsAt"] = time.time() + session.get("round_duration", 300)
            return player
    return None

def start_next_round(session_id, timer=300):
    s = sessions.get(session_id)
    if not s:
        return None
    s["round"] += 1
    s["problem_id"] += 1
    s["status"] = "active"
    s["winnerId"] = None
    s["round_duration"] = timer or s.get("round_duration", 300)
    s["roundEndsAt"] = time.time() + s["round_duration"]
    for p in s["players"]:
        if p:
            p["code"] = ""
    return s
