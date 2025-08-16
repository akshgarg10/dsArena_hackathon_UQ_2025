from flask import Blueprint, request, jsonify
from flask_cors import CORS, cross_origin
from utils.sessions import create_session, join_session, sessions, start_next_round
import time, subprocess, tempfile, os


match_bp = Blueprint("match", __name__)

CORS(match_bp, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"]
    }
})

@match_bp.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin")
    if origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Max-Age"] = "86400"
    return resp

@match_bp.route("/create", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], methods=["POST", "OPTIONS"])
def create_match():
    data = request.json
    player1 = data.get("player1")
    if not player1:
        return jsonify({"error": "Player name required"}), 400
    session_id, session_data = create_session(player1)
    return jsonify({
        "success": True,
        "sessionId": session_id,
        "players": session_data["players"],
        "round": session_data.get("round", 1),
        "status": session_data.get("status", "active"),
        "problemId": session_data.get("problem_id", 1)
    })

@match_bp.route("/join", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], methods=["POST", "OPTIONS"])
def join_match():
    data = request.json
    session_id = data.get("sessionId")
    player_name = data.get("playerName")
    if not session_id or not player_name:
        return jsonify({"error": "Session ID and player name required"}), 400
    player = join_session(session_id, player_name)
    if player:
        return jsonify({"success": True, "playerId": player["id"]})
    return jsonify({"error": "Session full or not found"}), 400

# ----- ADD THESE TWO ROUTES *ABOVE* the "/<session_id>" route -----
@match_bp.route("/run", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], methods=["POST", "OPTIONS"])
def run_code():
    data = request.json or {}
    code = data.get("code")
    session_id = data.get("sessionId")
    player_id = data.get("playerId")

    if not code:
        return jsonify({"error": "No code submitted"}), 400
    if not session_id or not player_id:
        return jsonify({"error": "Missing sessionId or playerId"}), 400

    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    pid = session.get("problem_id", 1)
    try:
        final_code = build_template(pid, code)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(final_code.encode())
            tmp.flush()
            tmp_path = tmp.name

        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        os.remove(tmp_path)

        output = result.stdout or result.stderr or ""
        has_tests = "Test " in output
        all_pass = has_tests and ("FAIL" not in output) and ("ERROR" not in output)

        game_ended = False
        winner_id = session.get("winnerId")
        if all_pass and session.get("status") not in ("ended", "completed"):
            session["status"] = "ended"
            session["winnerId"] = player_id
            game_ended = True
            winner_id = player_id
            # score
            for p in session["players"]:
                if p and p.get("id") == player_id:
                    p["score"] = p.get("score", 0) + 1
            # last round?
            if session.get("round", 1) >= session.get("roundsTotal", 5):
                session["status"] = "completed"
                p0, p1 = session["players"]
                s0, s1 = p0.get("score",0), p1.get("score",0)
                if s0 > s1: session["championId"] = p0["id"]
                elif s1 > s0: session["championId"] = p1["id"]
                else: session["championId"] = winner_id  # tie → last winner

        return jsonify({
            "output": output,
            "all_pass": all_pass,
            "gameEnded": game_ended or session.get("status") in ("ended", "completed"),
            "winnerId": winner_id,
            "status": session.get("status"),
            "round": session.get("round", 1),
            "problemId": pid,
        })

    except subprocess.TimeoutExpired:
        return jsonify({"output": "Error: Code execution timed out", "all_pass": False}), 400
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}", "all_pass": False}), 400


@match_bp.route("/next-round", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], methods=["POST", "OPTIONS"])
def next_round():
    data = request.json or {}
    session_id = data.get("sessionId")
    if not session_id:
        return jsonify({"error": "Missing sessionId"}), 400
    s = sessions.get(session_id)
    if not s:
        return jsonify({"error": "Session not found"}), 404
    if s.get("status") == "completed":
        return jsonify({"error": "Match completed"}), 400
    if s.get("status") != "ended":
        return jsonify({"error": "Round is still active"}), 400
    if s.get("round", 1) >= s.get("roundsTotal", 5):
        return jsonify({"error": "No more rounds"}), 400

    updated = start_next_round(session_id, timer=s.get("round_duration", 300))
    pid = updated["problem_id"]; prob = PROBLEMS.get(pid, {})
    return jsonify({
        "success": True,
        "round": updated["round"],
        "problemId": pid,
        "status": updated["status"],
        "winnerId": updated["winnerId"],
        "players": updated["players"],
        "timer": updated["round_duration"],
        "problem": {
            "title": prob.get("title"),
            "signature": prob.get("signature"),
            "statement": prob.get("statement"),
            "starter": prob.get("starter"),
            "slug": prob.get("slug"),
        }
    })
# ----- keep your dynamic GET route *after* these -----


@match_bp.route("/<session_id>", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], methods=["GET", "OPTIONS"])
def get_match(session_id):
    session = sessions.get(session_id)
    if session:
        ends_at = session.get("roundEndsAt")
        remaining = 0
        if session.get("status") == "active" and ends_at:
            remaining = max(0, int(ends_at - time.time()))
        pid = session.get("problem_id", 1)
        prob = PROBLEMS.get(pid, {})
        return jsonify({
            "players": session["players"],
            "status": session.get("status", "active"),
            "winnerId": session.get("winnerId"),
            "championId": session.get("championId"),
            "round": session.get("round", 1),
            "roundsTotal": session.get("roundsTotal", 5),
            "problemId": pid,
            "problem": {
                "title": prob.get("title"),
                "signature": prob.get("signature"),
                "statement": prob.get("statement"),
                "starter": prob.get("starter"),
                "slug": prob.get("slug"),
            },
            "remaining": remaining,
            "roundEndsAt": ends_at
        })
    return jsonify({"error": "Session not found"}), 404

PROBLEMS = {
    1: {
        "slug": "two-sum",
        "title": "Two Sum",
        "signature": "def two_sum(nums, target) -> list[int]:",
        "statement": "Return indices of two numbers such that they add to target.",
        "starter": "def two_sum(nums, target):\n    # return [i, j]\n    pass\n",
        "tests": [
            {"nums":[2,7,11,15], "target":9,  "exp":[0,1]},
            {"nums":[3,2,4],     "target":6,  "exp":[1,2]},
            {"nums":[3,3],       "target":6,  "exp":[0,1]},
        ],
        "func": "two_sum"
    },
    2: {
        "slug": "binary-search",
        "title": "Binary Search",
        "signature": "def binary_search(nums, target) -> int:",
        "statement": "Return index of target in sorted nums, or -1 if not found.",
        "starter": "def binary_search(nums, target):\n    # return index or -1\n    pass\n",
        "tests": [
            {"nums":[-1,0,3,5,9,12], "target":9,  "exp":4},
            {"nums":[-1,0,3,5,9,12], "target":2,  "exp":-1},
            {"nums":[1],             "target":1,  "exp":0},
        ],
        "func": "binary_search"
    },
    3: {
        "slug": "trapping-rain-water",
        "title": "Trapping Rain Water",
        "signature": "def trap(height) -> int:",
        "statement": "Given elevation map, compute total trapped water.",
        "starter": "def trap(height):\n    # return int\n    pass\n",
        "tests": [
            {"height":[0,1,0,2,1,0,1,3,2,1,2,1], "exp":6},
            {"height":[4,2,0,3,2,5],             "exp":9},
            {"height":[1,2,3],                   "exp":0},
        ],
        "func": "trap"
    },
    4: {
        "slug": "palindrome",
        "title": "Valid Palindrome",
        "signature": "def is_palindrome(s) -> bool:",
        "statement": "Check if string is a palindrome (alphanumeric, case-insensitive).",
        "starter": "def is_palindrome(s):\n    # return True/False\n    pass\n",
        "tests": [
            {"s":"A man, a plan, a canal: Panama", "exp":True},
            {"s":"race a car",                      "exp":False},
            {"s":"",                                "exp":True},
        ],
        "func": "is_palindrome"
    },
    5: {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "signature": "def is_valid(s) -> bool:",
        "statement": "Check if brackets ()[]{} are balanced.",
        "starter": "def is_valid(s):\n    # return True/False\n    pass\n",
        "tests": [
            {"s":"()",     "exp":True},
            {"s":"()[]{}", "exp":True},
            {"s":"(]",     "exp":False},
            {"s":"([)]",   "exp":False},
            {"s":"{[]}",   "exp":True},
        ],
        "func": "is_valid"
    },
}

def build_template(problem_id, user_code):
    p = PROBLEMS.get(problem_id)
    if not p:
        raise ValueError(f"No problem for id {problem_id}")
    func = p["func"]

    if problem_id == 1:  # two sum
        tests_lines = [
            f"tests.append(({{'nums':{t['nums']},'target':{t['target']}}}, {t['exp']}))"
            for t in p["tests"]
        ]
        tests_py = "\n".join("    " + line for line in tests_lines)
        harness = f"""
{user_code}

def _norm(ans):
    try:
        return list(ans)
    except Exception:
        return ans

if __name__ == "__main__":
    tests = []
{tests_py}
    for i, (inp, exp) in enumerate(tests, 1):
        try:
            got = _norm({func}(inp['nums'], inp['target']))
            ok = isinstance(got, list) and len(got) == 2 and sorted(got) == sorted(exp)
            print(f"Test {{i}}: {{'PASS' if ok else 'FAIL'}} (got={{got}}, expected={{exp}})")
        except Exception as e:
            print(f"Test {{i}}: ERROR ({{str(e)}})")
"""
        return harness

    elif problem_id == 2:  # binary search
        tests_lines = [
            f"tests.append(({t['nums']}, {t['target']}, {t['exp']}))"
            for t in p["tests"]
        ]
        tests_py = "\n".join("    " + line for line in tests_lines)
        harness = f"""
{user_code}

if __name__ == "__main__":
    tests = []
{tests_py}
    for i, (nums, target, exp) in enumerate(tests, 1):
        try:
            got = {func}(nums, target)
            ok = (got == exp)
            print(f"Test {{i}}: {{'PASS' if ok else 'FAIL'}} (got={{got}}, expected={{exp}})")
        except Exception as e:
            print(f"Test {{i}}: ERROR ({{str(e)}})")
"""
        return harness

    elif problem_id == 3:  # trap water
        tests_lines = [
            f"tests.append(({t['height']}, {t['exp']}))"
            for t in p["tests"]
        ]
        tests_py = "\n".join("    " + line for line in tests_lines)
        harness = f"""
{user_code}

if __name__ == "__main__":
    tests = []
{tests_py}
    for i, (height, exp) in enumerate(tests, 1):
        try:
            got = {func}(height)
            ok = (got == exp)
            print(f"Test {{i}}: {{'PASS' if ok else 'FAIL'}} (got={{got}}, expected={{exp}})")
        except Exception as e:
            print(f"Test {{i}}: ERROR ({{str(e)}})")
"""
        return harness

    elif problem_id == 4:  # palindrome
        tests_lines = [
            f"tests.append(({t['s']!r}, {t['exp']}))"
            for t in p["tests"]
        ]
        tests_py = "\n".join("    " + line for line in tests_lines)
        harness = f"""
{user_code}

import re
def _clean(x): return re.sub(r'[^0-9a-zA-Z]', '', x).lower()

if __name__ == "__main__":
    tests = []
{tests_py}
    for i, (s, exp) in enumerate(tests, 1):
        try:
            got = {func}(s)
            ok = (got is True and _clean(s) == _clean(s)[::-1]) or (got == exp)
            print(f"Test {{i}}: {{'PASS' if ok else 'FAIL'}} (got={{got}}, expected={{exp}})")
        except Exception as e:
            print(f"Test {{i}}: ERROR ({{str(e)}})")
"""
        return harness

    elif problem_id == 5:  # valid parentheses
        tests_lines = [
            f"tests.append(({t['s']!r}, {t['exp']}))"
            for t in p["tests"]
        ]
        tests_py = "\n".join("    " + line for line in tests_lines)
        harness = f"""
{user_code}

if __name__ == "__main__":
    tests = []
{tests_py}
    for i, (s, exp) in enumerate(tests, 1):
        try:
            got = {func}(s)
            ok = (got == exp)
            print(f"Test {{i}}: {{'PASS' if ok else 'FAIL'}} (got={{got}}, expected={{exp}})")
        except Exception as e:
            print(f"Test {{i}}: ERROR ({{str(e)}})")
"""
        return harness

    else:
        raise ValueError("unhandled problem id")
