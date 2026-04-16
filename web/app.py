from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from web.models import db, User, Vote
from werkzeug.security import generate_password_hash, check_password_hash
import json

from crypto import keygen
from bulletin_board import BulletinBoard
from auth import AuthServer
from verify_server import VotingServer  # renamed module

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.secret_key = "dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

    # 1. check auth
    user_id = current_user.id

    # 2. check if already voted
    existing = Vote.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({"status": "rejected", "reason": "already voted"})

    # 3. call crypto system (your existing logic)
    result = voting.submit_ballot(data)

    if result:
        # 4. record vote
        vote = Vote(user_id=user_id, ballot_hash = json.dumps(data.get("ciphertext")))
        db.session.add(vote)
        db.session.commit()

    return jsonify({"status": "accepted" if result else "rejected"})


# -----------------------------
# API: bulletin board (public ballots)
# -----------------------------
@app.route("/api/board", methods=["GET"])
def get_board():
    votes = Vote.query.all()

    return jsonify([
        {
            "ciphertext": json.loads(v.ballot_hash),
            "hash": v.ballot_hash
        }
        for v in votes
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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return "User already exists", 400

        new_user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            return render_template(
                "login.html",
                error="Invalid credentials, try again",
                username=username
            )

        login_user(user)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("home"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/vote")
@login_required
def vote_page():
    return render_template("vote.html")

@app.route("/board")
def board_page():
    return render_template("board.html")

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)