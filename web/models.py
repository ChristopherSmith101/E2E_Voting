from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    token_hash = db.Column(db.String(256), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    ballot_hash = db.Column(db.String(256))