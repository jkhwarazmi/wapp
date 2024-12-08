"""Configures the Flask app."""

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(basedir, ".env"))

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = True

SECRET_KEY = os.environ.get("SECRET_KEY")
WTF_CSRF_ENABLED = True

TMDB_KEY = os.environ.get("TMDB_KEY")
