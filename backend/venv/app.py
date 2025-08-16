# app.py
from flask import Flask
from flask_cors import CORS
from routes.match import match_bp

app = Flask(__name__)

# Allow your Vite dev server origins for all /api/* endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False,
    }
})

app.register_blueprint(match_bp, url_prefix="/api/match")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
