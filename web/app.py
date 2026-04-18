from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from web.models import db, User, Vote
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import hashlib
from authlib.integrations.flask_client import OAuth
from crypto import keygen
from bulletin_board import BulletinBoard
from auth import AuthServer
from verify_server import VotingServer
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
# Global election state (simple prototype)
# -----------------------------
sk, pk = keygen()  # RESETS WHEN SERVER RESTARTS, MUST BE CHANGED!!!!!!!!!!!!!!!!!!!!
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
@login_required
def issue_token():
    if current_user.has_voted:
        return jsonify({"error": "Already voted"}), 403
    token = auth.issue_token()
    return jsonify({"token": token})

# -----------------------------
# API: submit encrypted ballot
# -----------------------------
@app.route("/api/vote", methods=["POST"])
@login_required
def submit_vote():
    data = request.get_json()
    token = data.get("token")
    ciphertext = data.get("ciphertext")
    
    # -------------------------
    # 1. Validate token
    # -------------------------
    if not auth.validate_token(token):
        return jsonify({"status": "rejected"})
    
    # -------------------------
    # 2. Hash token (receipt)
    # -------------------------
    token_hash = auth.hash_token(token)
    
    # -------------------------
    # 3. Compute ballot hash (NEW)
    # -------------------------
    ballot_hash_digest = hashlib.sha256(
        json.dumps(ciphertext, sort_keys=True).encode()
    ).hexdigest()
    
    # -------------------------
    # 4. Store vote
    # -------------------------
    vote = Vote(
        token_hash=token_hash,
        ballot_hash=json.dumps(ciphertext),
        ballot_hash_digest=ballot_hash_digest  # NEW
    )
    db.session.add(vote)
    
    # -------------------------
    # 5. Mark user as voted
    # -------------------------
    current_user.has_voted = True
    db.session.commit()
    
    # -------------------------
    # 6. Return receipt WITH ballot hash (NEW)
    # -------------------------
    return jsonify({
        "status": "accepted",
        "receipt": token_hash,
        "ballot_hash": ballot_hash_digest  # NEW
    })

# -------------------------
# API: verify individual ballot (NEW)
# -------------------------
@app.route("/api/verify", methods=["POST"])
def verify_ballot():
    """Voter provides receipt + ballot_hash to verify their ballot is recorded"""
    data = request.get_json()
    receipt = data.get("receipt")
    provided_hash = data.get("ballot_hash")
    
    # Find ballot on board
    vote = Vote.query.filter_by(token_hash=receipt).first()
    if not vote:
        return jsonify({"status": "not_found", "message": "Ballot not found"}), 404
    
    # Verify hash matches
    if vote.ballot_hash_digest != provided_hash:
        return jsonify({
            "status": "failed",
            "message": "Ballot was tampered with!"
        }), 400
    
    return jsonify({
        "status": "verified",
        "message": "Your ballot is recorded on the bulletin board",
        "receipt": receipt,
        "timestamp": vote.timestamp.isoformat() if vote.timestamp else None
    })

# -------------------------
# API: bulletin board (public ballots)
# -------------------------
@app.route("/api/board", methods=["GET"])
def get_board():
    votes = Vote.query.all()
    return jsonify([
        {
            "receipt": v.token_hash,
            "ciphertext": json.loads(v.ballot_hash),
            "ballot_hash": v.ballot_hash_digest  # NEW
        }
        for v in votes
    ])

# -------------------------
# API: tally result (demo only)
# -------------------------
@app.route("/api/results", methods=["GET"])
def results():
    from tally import tally
    result = tally(board.list_ballots(), sk)
    return jsonify({"result": result})

# -------------------------
# API: get current_user voting state
# -------------------------
@app.route("/api/status", methods=["GET"])
@login_required
def status():
    return jsonify({
        "has_voted": current_user.has_voted
    })

# -------------------------
# OAuth Routes
# -------------------------
@app.route("/auth/start")
def auth_start():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    userinfo = google.userinfo()
    email = userinfo["email"]
    google_id = userinfo["sub"]
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            username=email
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("home"))

# -------------------------
# Simple frontend entries
# -------------------------
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
        return redirect(url_for("login_page"))
    return render_template("register.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login_page"))

@app.route("/vote")
@login_required
def vote_page():
    return render_template("vote.html")

@app.route("/board")
def board_page():
    return render_template("board.html")

# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)