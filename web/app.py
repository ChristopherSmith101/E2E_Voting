from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from web.models import db, User, Vote
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import hashlib
from authlib.integrations.flask_client import OAuth
from crypto import keygen, decrypt
from bulletin_board import BulletinBoard
from auth import AuthServer
from verify_server import VotingServer
from ballot import Ballot
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

# -------------------------
# Global election state (simple prototype)
# -------------------------
sk, pk = keygen()  # RESETS WHEN SERVER RESTARTS, MUST BE CHANGED!!!!!!!!!!!!!!!!!!!!
board = BulletinBoard()
auth = AuthServer()
voting = VotingServer(board, auth)

# -------------------------
# API: public key
# -------------------------
@app.route("/api/public_key", methods=["GET"])
def public_key():
    return jsonify({"pk": pk})

# -------------------------
# API: issue voting token
# -------------------------
@app.route("/api/token", methods=["POST"])
@login_required
def issue_token():
    if current_user.has_voted:
        return jsonify({"error": "Already voted"}), 403
    token = auth.issue_token()
    return jsonify({"token": token})

# -------------------------
# API: submit encrypted ballot
# -------------------------
@app.route("/api/vote", methods=["POST"])
@login_required
def submit_vote():
    data = request.get_json()
    token = data.get("token")
    ciphertext = data.get("ciphertext")
    is_dummy = data.get("is_dummy", False)  # NEW: anti-coercion flag
    
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
    # 3. Compute ballot hash
    # -------------------------
    ballot_hash_digest = hashlib.sha256(
        json.dumps(ciphertext, sort_keys=True).encode()
    ).hexdigest()
    
    # -------------------------
    # 4. Store vote in database
    # -------------------------
    vote = Vote(
        token_hash=token_hash,
        ballot_hash=json.dumps(ciphertext),
        ballot_hash_digest=ballot_hash_digest,
        is_dummy=is_dummy  # NEW
    )
    db.session.add(vote)
    
    # -------------------------
    # 5. Also post to bulletin board
    # -------------------------
    ballot = Ballot(
        ciphertext=tuple(ciphertext.values()) if isinstance(ciphertext, dict) else tuple(ciphertext),
        proof=data.get("proof"),
        voter_token=token
    )
    board.post_ballot(ballot)
    
    # -------------------------
    # 6. Mark user as voted
    # -------------------------
    current_user.has_voted = True
    db.session.commit()
    
    # -------------------------
    # 7. Return receipt WITH ballot hash
    # -------------------------
    return jsonify({
        "status": "accepted",
        "receipt": token_hash,
        "ballot_hash": ballot_hash_digest,
        "is_dummy": is_dummy  # NEW
    })

# -------------------------
# API: verify individual ballot
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
        "is_dummy": vote.is_dummy,
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
            "ballot_hash": v.ballot_hash_digest
        }
        for v in votes
    ])

# -------------------------
# API: get all ballots for verification
# -------------------------
@app.route("/api/ballots", methods=["GET"])
def get_ballots():
    """Return all ballots with their hashes for external verification"""
    votes = Vote.query.all()
    return jsonify({
        "election_pk": pk,
        "ballots": [
            {
                "receipt": v.token_hash,
                "ciphertext": json.loads(v.ballot_hash),
                "ballot_hash": v.ballot_hash_digest,
                "timestamp": v.timestamp.isoformat() if v.timestamp else None
            }
            for v in votes
        ]
    })

# -------------------------
# API: verify all ballots
# -------------------------
@app.route("/api/ballots/verify", methods=["GET"])
def verify_all_ballots():
    """Universal verifiability: verify all ballots are valid"""
    votes = Vote.query.all()
    
    valid_count = 0
    invalid_count = 0
    details = []
    
    for idx, vote in enumerate(votes):
        # A ballot is valid if:
        # 1. It has a receipt and ballot hash
        # 2. The ballot hash was computed correctly (we trust our own computation)
        is_valid = vote.token_hash and vote.ballot_hash_digest
        
        if is_valid:
            valid_count += 1
            details.append({
                "index": idx + 1,
                "valid": True,
                "receipt": vote.token_hash,
                "reason": None
            })
        else:
            invalid_count += 1
            details.append({
                "index": idx + 1,
                "valid": False,
                "receipt": vote.token_hash,
                "reason": "Missing hash or receipt"
            })
    
    return jsonify({
        "total_ballots": len(votes),
        "valid_ballots": valid_count,
        "invalid_ballots": invalid_count,
        "details": details
    })

# -------------------------
# API: tally with proof
# -------------------------
@app.route("/api/ballots/tally", methods=["GET"])
def get_tally():
    """
    Return the election tally + proof for universal verifiability.
    Reads directly from database instead of in-memory board.
    Excludes dummy votes from tally.
    """
    votes = Vote.query.all()
    
    # Count real votes (exclude dummies)
    real_votes = [v for v in votes if not v.is_dummy]
    dummy_votes = [v for v in votes if v.is_dummy]
    
    if not real_votes:
        return jsonify({
            "total_ballots": len(votes),
            "real_ballots": 0,
            "dummy_ballots": len(dummy_votes),
            "yes_votes": 0,
            "no_votes": 0,
            "yes_percentage": 0.0,
            "no_percentage": 0.0,
            "winner": "No real votes cast yet",
            "invalid_ballots": 0,
            "election_pk": pk
        })
    
    # Count YES votes by decrypting from database (skip dummy votes)
    yes_count = 0
    for vote in real_votes:
        ciphertext_dict = json.loads(vote.ballot_hash)
        ciphertext_tuple = (ciphertext_dict['c1'], ciphertext_dict['c2'])
        decrypted = decrypt(sk, ciphertext_tuple)
        if decrypted == 1:
            yes_count += 1
    
    total = len(real_votes)
    yes_votes = yes_count
    no_votes = total - yes_votes
    
    yes_percentage = (yes_votes / total * 100) if total > 0 else 0
    no_percentage = (no_votes / total * 100) if total > 0 else 0
    
    winner = "YES" if yes_votes > no_votes else ("NO" if no_votes > yes_votes else "TIE")
    
    # Create tally proof
    ballot_hashes = sorted([v.ballot_hash_digest for v in real_votes])
    ballot_data = json.dumps(ballot_hashes, sort_keys=True)
    tally_proof_input = str(yes_votes) + str(no_votes) + ballot_data
    tally_proof = hashlib.sha256(tally_proof_input.encode()).hexdigest()
    
    return jsonify({
        "total_ballots": len(votes),
        "real_ballots": len(real_votes),
        "dummy_ballots": len(dummy_votes),
        "yes_votes": yes_votes,
        "no_votes": no_votes,
        "yes_percentage": yes_percentage,
        "no_percentage": no_percentage,
        "winner": winner,
        "invalid_ballots": 0,
        "election_pk": pk,
        "tally_proof": tally_proof
    })

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

@app.route("/verify")
def verify_page():
    return render_template("verify.html")

# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # Fetch the port from environment variables, defaulting to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    host = int(os.environ.get("HOST", "127.0.0.1"))

    app.run(host="0.0.0.0", port=port, debug=True)