from app import app
import re

TMDB_KEY = app.config["TMDB_KEY"]
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_KEY}"
}

USERNAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]{0,29}$")
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@"
    r"[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"\.[a-zA-Z]{2,}$"
)
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])[A-Za-z\d\W_]{8,24}$")