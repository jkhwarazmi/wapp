"""Database models for the application."""

from app import db, login
from datetime import datetime, timezone
from random import choice
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash


PROFILE_COLOURS = {
    "#3375cb": "Dark Blue",
    "#51b1df": "Light Blue",
    "#59c3ad": "Turquoise",
    "#5fcf80": "Green",
    "#7a5ddf": "Purple",
    "#959595": "Grey",
    "#c67b2b": "Orange",
    "#c89332": "Yellow",
    "#c22946": "Red",
    "#d7348a": "Pink"
}


@login.user_loader
def load_user(id):
    """Load the user by ID."""
    return User.query.get(int(id))


class User(db.Model):
    """User model."""

    id = db.Column(db.Integer, primary_key=True)

    # Unique so watch parties still work even if user deleted
    username = db.Column(db.String(30), unique=True,
                         nullable=False, index=True)

    # Not unique to allow for deletion
    email = db.Column(db.String(256), nullable=False)

    # Nullable to allow for deletion
    password_hash = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, default=datetime.now(
        timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, default=None, index=True)
    profile_colour = db.Column(db.String(7), default=lambda: choice(
        list(PROFILE_COLOURS.keys())), nullable=False)

    watch_parties_created = db.relationship(
        "WatchParty", backref="creator", lazy="dynamic")
    watch_parties_joined = db.relationship(
        "WatchPartyUser", backref="user", lazy="dynamic")
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    reactions = db.relationship(
        "CommentReaction", backref="user", lazy="dynamic")

    def set_password(self, password):
        """Set the password for the user."""
        self.password_hash = generate_password_hash(password, method="pbkdf2")

    def check_password(self, password):
        """Check the password for the user."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        """Check if the user is not deleted."""
        return self.deleted_at is None

    def get_id(self):
        """Get the user ID."""
        return self.id

    def is_authenticated(self):
        """Check if the user is authenticated."""
        return True

    def is_anonymous(self):
        """Check if the user is anonymous."""
        return False


class WatchParty(db.Model):
    """Watch Party Model."""

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(32), unique=True,
                    default=lambda: uuid4().hex, nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500))
    location = db.Column(db.String(100))
    start_time = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                           nullable=False)
    created_by = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False)
    deleted_at = db.Column(db.DateTime, default=None, index=True)
    is_private = db.Column(db.Boolean, default=False, nullable=False)

    watch_party_users = db.relationship(
        "WatchPartyUser", backref="watch_party", lazy="dynamic")
    comments = db.relationship(
        "Comment", backref="watch_party", lazy="dynamic")


class WatchPartyUser(db.Model):
    """Watch Party User Model."""

    __table_args__ = (
        db.UniqueConstraint("user_id", "watch_party_id",
                            name="uix_user_watch_party"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    watch_party_id = db.Column(db.Integer, db.ForeignKey(
        "watch_party.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.now(
        timezone.utc), nullable=False)
    rating = db.Column(db.Integer, default=None)


class Comment(db.Model):
    """Watch Party Comment Model."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    watch_party_id = db.Column(db.Integer, db.ForeignKey(
        "watch_party.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, default=None, index=True)

    reactions = db.relationship(
        "CommentReaction", backref="comment", lazy="dynamic")


class CommentReaction(db.Model):
    """Watch Party Comment Reaction Model."""

    __table_args__ = (
        db.UniqueConstraint("user_id", "comment_id",
                            name="uix_user_comment_reaction"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey(
        "comment.id"), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)
