from dotenv import load_dotenv
load_dotenv()
import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

GAPGPT_API_KEY = os.environ.get("GAPGPT_API_KEY", "")
BALE_BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")

GAPGPT_URL = "https://api.gapgpt.app/v1/chat/completions"
BALE_URL = "https://tapi.bale.ai"

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/chess-ai", methods=["POST"])
def chess_ai():
    if not GAPGPT_API_KEY:
        return jsonify({"error": "GAPGPT_API_KEY is not configured"}), 500

    data = request.get_json(silent=True) or {}

    fen = data.get("fen", "")
    history = data.get("history", [])
    legal_moves = data.get("legalMoves", [])

    system_prompt = """You are an extremely strong chess move selector.

You are playing a real chess game.

You MUST understand the exact current board from the FEN and the complete previous move history.

Analyze:
- tactics
- checks
- captures
- threats
- king safety
- material
- development
- promotion
- castling
- positional consequences
- previous moves

You MUST choose exactly one move from the supplied legal moves.

Never invent a move.
Never return an illegal move.

Return ONLY valid JSON:
{"move":"e2e4"}

No markdown.
No explanation.
No extra text."""

    user_prompt = {
        "current_fen": fen,
        "previous_moves": history,
        "legal_moves": legal_moves
    }

    try:
        r = requests.post(
            GAPGPT_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + GAPGPT_API_KEY
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": str(user_prompt)
                    }
                ],
                "temperature": 0,
                "max_tokens": 40,
                "stream": False
            },
            timeout=30
        )

        return (r.text, r.status_code, {
            "Content-Type": "application/json"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/send-photo", methods=["POST"])
def send_photo():
    if not BALE_BOT_TOKEN:
        return jsonify({"error": "BALE_BOT_TOKEN is not configured"}), 500

    data = request.get_json(silent=True) or {}

    chat_id = data.get("chat_id")
    photo_url = data.get("photo_url")
    caption = data.get("caption", "")

    if not chat_id or not photo_url:
        return jsonify({
            "error": "chat_id and photo_url are required"
        }), 400

    try:
        r = requests.post(
            f"{BALE_URL}/bot{BALE_BOT_TOKEN}/sendPhoto",
            json={
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption
            },
            timeout=30
        )

        return (r.text, r.status_code, {
            "Content-Type": "application/json"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/profile-photo/<user_id>", methods=["GET"])
def profile_photo(user_id):
    if not BALE_BOT_TOKEN:
        return jsonify({"error": "BALE_BOT_TOKEN is not configured"}), 500

    try:
        r = requests.get(
            f"{BALE_URL}/bot{BALE_BOT_TOKEN}/getUserProfilePhotos",
            params={
                "user_id": user_id,
                "limit": 1
            },
            timeout=30
        )

        return (r.text, r.status_code, {
            "Content-Type": "application/json"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
