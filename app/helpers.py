"""Helper functions for the app."""

from flask import flash, redirect, url_for, abort
from app import app, models
from flask_login import current_user
import requests
from datetime import datetime, date, time
from random import sample
from .constants import headers


def get_random_movies():
    """Get 5 random movies from the past 2 years."""
    current_year = datetime.now().year

    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "include_adult": False,
        "include_video": False,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "primary_release_date.gte": f"{current_year-2}-01-01",
        "primary_release_date.lte": f"{current_year}-12-31",
        "vote_count.gte": 100,
        "with_poster": True,
        "page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # Randomly shuffle and select 5 movies
    selected = sample(data["results"], 5)
    movies = [{
        "title": movie["title"],
        "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    } for movie in selected]

    return movies


def validate_party(
        title, movie_id, description, location,
        start_date, start_time, is_private):
    """Validate the Watch Party form."""
    # Check types
    if not title or not isinstance(title, str):
        app.logger.debug(
            f"Wrong Watch Party title type by {current_user.username}")
        return "Invalid title."

    if not movie_id or not isinstance(movie_id, int):
        app.logger.debug(
            f"Wrong Watch Party movie ID type by {current_user.username}")
        return "Invalid movie ID."

    if description and not isinstance(description, str):
        app.logger.debug(
            f"Wrong Watch Party description type by {current_user.username}")
        return "Invalid description."

    if location and not isinstance(location, str):
        app.logger.debug(
            f"Wrong Watch Party location type by {current_user.username}")
        return "Invalid location."

    # Convert string dates to datetime objects if they aren't already
    if not isinstance(start_date, date):
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            app.logger.debug(
                f"Wrong Watch Party start date by {current_user.username}")
            return "Invalid start date."

    if not isinstance(start_time, time):
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
        except (ValueError, TypeError):
            app.logger.debug(
                f"Wrong Watch Party start time by {current_user.username}")
            return "Invalid start time."

    if is_private not in [True, False]:
        app.logger.debug(
            f"Wrong Watch Party privacy type by {current_user.username}")
        return "Invalid privacy setting."

    # Combine date and time
    start = datetime.combine(start_date, start_time)
    now = datetime.now()

    # Check values
    if title.strip() == "":
        app.logger.debug(
            f"Empty title for Watch Party by {current_user.username}")
        return "Title cannot be empty."

    if len(title) > 100:
        app.logger.debug(
            f"Title too long for Watch Party by {current_user.username}")
        return "Title cannot be longer than 100 characters."

    if description and len(description) > 500:
        app.logger.debug(
            f"Description too long for Watch Party by {current_user.username}")
        return "Description cannot be longer than 500 characters."

    if location and len(location) > 100:
        app.logger.debug(
            f"Location too long for Watch Party by {current_user.username}")
        return "Location cannot be longer than 100 characters."

    if start < now:
        app.logger.debug(
            f"Past start for Watch Party by {current_user.username}")
        return "Start date cannot be in the past."

    if start > now.replace(year=now.year + 1):
        app.logger.debug(
            f"Too far start for Watch Party by {current_user.username}")
        return "Start date cannot be more than a year in the future."

    return start


def party_edit_allowed(watch_party):
    """Check if the user is allowed to edit a Watch Party."""
    if current_user.deleted_at is not None:
        app.logger.debug(
            f"""{current_user.username} tried editing a Watch Party with a """
            """deleted account, {watch_party.id}""")
        flash("Your account has been deleted", "warning")
        return redirect(url_for("auth.login"))

    if watch_party.created_by != current_user.id:
        app.logger.debug(
            f"""{current_user.username} tried to edit a Watch Party they """
            """do not own, {watch_party.id}""")
        flash("You are not the owner of this Watch Party", "warning")
        return redirect(url_for("party", url=watch_party.url))

    if watch_party.start_time < datetime.now():
        app.logger.debug(
            f"""{current_user.username} tried to edit a Watch Party that """
            """has already started, {watch_party.id}""")
        flash("You cannot modify a Watch Party that has started", "warning")
        return redirect(url_for("party", url=watch_party.url))

    return True


def party_check(url):
    """Check if a Watch Party exists."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    if not wp:
        app.logger.debug(
            f"""{current_user.username} tried to access a """
            """non-existent Watch Party, {url}""")
        flash("This Watch Party does not exist")
        abort(404)

    if wp.deleted_at is not None:
        app.logger.debug(
            f"""{current_user.username} tried to access a """
            """deleted Watch Party, {wp.id}""")
        flash("This Watch Party has been deleted", "warning")
        abort(404)

    return wp
