"""Contains the form input fields for the application."""

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, EmailField
from wtforms import IntegerField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import TextArea


class LoginForm(FlaskForm):
    """Form for logging in."""

    username = StringField("Username", validators=[
                           DataRequired(), Length(max=30)])
    password = PasswordField("Password", validators=[
                             DataRequired(), Length(min=8, max=24)])
    remember_me = BooleanField("Remember Me", default=False)


class RegisterForm(FlaskForm):
    """Form for registering a new user."""

    username = StringField("Username", validators=[
                           DataRequired(), Length(max=30)])
    email = EmailField("Email", validators=[
                       DataRequired(), Length(min=5, max=256)])
    password = PasswordField("Password", validators=[
                             DataRequired(), Length(min=8, max=24)])
    confirm_password = PasswordField("Confirm Password", validators=[
                                     DataRequired(), Length(min=8, max=24)])


class SearchForm(FlaskForm):
    """Form for searching for a movie."""

    search = StringField("Search", validators=[
                         DataRequired(), Length(max=100)])


class WatchPartyForm(FlaskForm):
    """Form for creating a new watch party."""

    title = StringField("Title", validators=[
                        DataRequired(), Length(min=1, max=100)])
    movie_id = IntegerField("Movie ID", validators=[DataRequired()])
    description = StringField("Description", widget=TextArea(), validators=[
                              Length(max=500)])
    location = StringField("Location", validators=[
                           Length(max=100)])
    start_date = DateField("Start Date", format="%Y-%m-%d",
                           validators=[DataRequired()])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    is_private = BooleanField("Private", default=False)


class RatingForm(FlaskForm):
    """Form for rating a movie."""

    rating = SelectField("Rating", validators=[DataRequired()], choices=[
                         (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])


class CommentForm(FlaskForm):
    """Form for commenting on a movie."""

    content = StringField("Comment", widget=TextArea(), validators=[
                          DataRequired(), Length(max=500)])
