"""Initialise the Flask application and the database."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler

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

handler = RotatingFileHandler("logfile.log", maxBytes=1000000, backupCount=1)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)
