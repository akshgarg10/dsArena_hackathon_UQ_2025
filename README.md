## Getting Started

### 1) Backend (Flask)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# Windows (PowerShell): .\venv\Scripts\Activate.ps1

pip install flask flask-cors

# run the server
python app.py  # listens on http://127.0.0.1:5000


#Front end
cd frontend
npm install

VITE_API_URL=http://127.0.0.1:5000/

VITE_API_URL=http://127.0.0.1:5000


# DSArena

A head-to-head coding arena where two players join the same session, solve a sequence of DSA problems, and race to pass all test cases first. Each match is 5 fixed rounds with live timer sync, winner/loser screens per round, and a final champion screen.

## Features
- Create / Join session (Player 1 creates, Player 2 joins via session ID)
- Live polling to keep both clients in sync (names, code mirror for P2, status, winner)
- 5 fixed rounds:
  1) Two Sum  
  2) Binary Search  
  3) Trapping Rain Water  
  4) Valid Palindrome  
  5) Valid Parentheses
- Backend compiles a per-round Python test harness and runs user code in a temp file
- Round ends automatically when a player passes all tests; last round produces a match champion
- Live countdown timer per round shown on both clients
- CORS configured for Vite dev server

## Tech Stack
- **Frontend:** React (Vite), Monaco Editor
- **Backend:** Flask, `flask-cors`
- **Runtime:** Python subprocess for sandboxed execution (with short timeout)

## Repo Layout
