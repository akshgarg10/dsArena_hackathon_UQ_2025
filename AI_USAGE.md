# AI Usage & Attribution

**Summary:** Approximately **70%** of this project’s code and troubleshooting was created with assistance from **OpenAI’s ChatGPT**. The human author(s) reviewed, adapted, and tested all AI-assisted code before committing it to the repository.

## Scope of AI Assistance
- **Frontend (React/Vite/Monaco)**
  - Page structure and state flow for session create/join, waiting screen, arena view
  - Timer sync logic and live updates
  - Code editor integration and run action / error surfacing
- **Backend (Flask)**
  - Route design for `/create`, `/join`, `/<session_id>`, `/run`, `/next-round`
  - Per-round Python test harness generation and subprocess execution with timeouts
  - CORS configuration for Vite dev origins
- **Game Logic**
  - Multi-round flow (fixed 5 rounds), win detection, round transitions
  - Score keeping and champion resolution
- **Debugging & DevOps**
  - Fixes for 405/400/404 issues, f-string escaping, indentation in generated harness
  - Git ignore patterns, line endings, WSL/Git setup notes

## Human Oversight
- All AI-generated suggestions were **manually reviewed** and edited for correctness, security, and readability.
- Final behavior was **tested locally** (frontend + backend) before commits.

## Tools & Model
- Assistant: **ChatGPT (OpenAI)**
- Usage: Iterative prompts for code generation, refactoring, and troubleshooting.

## Responsibility & License
Repository maintainers accept responsibility for the final code as committed.  
AI-assisted content is distributed under the project’s chosen license.

## Reproducibility
- Backend environment should be recreated via `python -m venv venv` and `pip install -r requirements.txt`.
- Frontend dependencies via `npm install`.
