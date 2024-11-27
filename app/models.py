"""Database model for the assessment table."""

from app import db
from datetime import datetime, timezone


class Assessment(db.Model):
    """Assessment model."""

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    due_time = db.Column(db.Time)
    desc = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now(
        timezone.utc), nullable=False)
    modified_at = db.Column(db.DateTime, default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, default=None, index=True)
    completed_at = db.Column(db.DateTime, default=None, index=True)
