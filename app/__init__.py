"""Initialise the Flask application and the database."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import logging

app = Flask(__name__)
app.config.from_object("config")
csrf = CSRFProtect(app)
db = SQLAlchemy(app)

migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "auth.login"
login.login_message = "Please log in to access this page."

# Avoid circular imports
from app import views, models
from app.auth import auth

app.register_blueprint(auth)


logging.basicConfig(filename="logfile.log", level=logging.DEBUG)
