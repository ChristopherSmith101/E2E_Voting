from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    google_id = db.Column(db.String(120), unique=True)
    has_voted = db.Column(db.Boolean, default=False, nullable=False)
    
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(256), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    ballot_hash = db.Column(db.String(256))
    ballot_hash_digest = db.Column(db.String(64))
    is_dummy = db.Column(db.Boolean, default=False)