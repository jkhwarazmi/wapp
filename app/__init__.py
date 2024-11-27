"""Initialise the Flask application and the database."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object("config")
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Avoid circular imports
from app import views, models
