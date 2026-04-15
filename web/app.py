from flask import Flask, request, jsonify, render_template
import sys

# allow imports from parent directory
sys.path.append("..")

from crypto import keygen
from bulletin_board import BulletinBoard
from auth import AuthServer
from verify_server import VotingServer  # renamed module

app = Flask(__name__)

# -----------------------------
# Global election state (simple prototype)
# -----------------------------
sk, pk = keygen() # RESETS WHEN SERVER RESTARTS, MUST BE CHANGED

board = BulletinBoard()
auth = AuthServer()
voting = VotingServer(board, auth)

# -----------------------------
# API: public key
# -----------------------------
@app.route("/api/public_key", methods=["GET"])
def public_key():
    return jsonify({"pk": pk})


# -----------------------------
# API: issue voting token
# -----------------------------
@app.route("/api/token", methods=["POST"])
def issue_token():
    token = auth.issue_token()
    return jsonify({"token": token})


# -----------------------------
# API: submit encrypted ballot
# -----------------------------
@app.route("/api/vote", methods=["POST"])
def submit_vote():
    data = request.get_json()
    print("INCOMING TOKEN:", data.get("token"))
    print("SERVER TOKENS:", auth.tokens)
    try:
        result = voting.submit_ballot(data)
        return jsonify({"status": "accepted" if result else "rejected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# -----------------------------
# API: bulletin board (public ballots)
# -----------------------------
@app.route("/api/board", methods=["GET"])
def get_board():
    ballots = board.list_ballots()

    # make JSON-safe output
    return jsonify([
        {
            "ciphertext": b.ciphertext,
            "proof": b.proof,
            "hash": b.hash()
        }
        for b in ballots
    ])


# -----------------------------
# API: tally result (demo only)
# -----------------------------
@app.route("/api/results", methods=["GET"])
def results():
    from tally import tally
    result = tally(board.list_ballots(), sk)
    return jsonify({"result": result})


# -----------------------------
# Simple frontend entries
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/vote")
def vote_page():
    return render_template("vote.html")


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)