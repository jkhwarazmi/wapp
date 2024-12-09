"""Authentication related routes."""

from flask import render_template, flash, redirect, url_for, request, Blueprint
from app import app, db, models
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from .forms import LoginForm, RegisterForm
from .constants import USERNAME_REGEX, EMAIL_REGEX, PASSWORD_REGEX


auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Render the login page and handle login requests."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        remember_me = form.remember_me.data
        password = form.password.data

        error = None
        user = db.session.query(models.User).filter_by(
            username=username).first()

        # Check if the user exists and the password is correct
        if user is None or user.deleted_at is not None:
            error = "Invalid username"
            app.logger.info(f"User {username} does not exist")
        elif not user.check_password(password):
            error = "Invalid password"
            app.logger.info(f"User {username} entered an invalid password")

        if error is None:
            login_user(user, remember=bool(remember_me))
            app.logger.info(f"User {username} logged in")

            # If requested page required authentication, redirect them there
            next_page = request.args.get("next")

            # Check for malicious redirects
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("index")
                app.logger.warning(
                    f"User {username} attempted to redirect to {next_page}")

            return redirect(next_page)
        else:
            flash(error)

    return render_template("login.html", title="Login", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Render the register page and handle registration requests."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        length = len(email)
        password = form.password.data
        confirm = form.confirm_password.data

        error = None
        if not username:
            error = "Username is required"
        elif not USERNAME_REGEX.match(username):
            error = "Username is invalid"
        elif not email:
            error = "Email is required"
        elif not EMAIL_REGEX.match(email) or length > 256 or length < 5:
            error = "Email is invalid"
        elif not password:
            error = "Password is required"
        elif not PASSWORD_REGEX.match(password):
            error = "Password is invalid"
        elif password != confirm:
            error = "Passwords must match"
        elif db.session.query(models.User).filter(
                models.User.username == username).first():
            error = "Username already taken"
        elif db.session.query(models.User).filter(
                models.User.email == email,
                models.User.deleted_at is None
        ).first():
            error = "Email already taken"

        if error is None:
            user = models.User(username=username, email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user)
            app.logger.info(f"User {username} registered and logged in")
            return redirect(url_for("index"))
        else:
            flash(error)
            app.logger.info(f"Failed to register user {username}. {error}")

    return render_template("register.html", title="Register", form=form)


@auth.route("/logout")
def logout():
    """Log the user out."""
    if current_user.is_authenticated:
        app.logger.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for("index"))
