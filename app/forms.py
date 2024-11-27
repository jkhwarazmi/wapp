"""Contains the form input fields for the application."""

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import TextArea


class AssessmentForm(FlaskForm):
    """Form for creating a new assessment or editing an existing one."""

    module = StringField("Module", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    due_date = DateField("Due Date", format="%Y-%m-%d",
                         validators=[DataRequired()])
    due_time = TimeField("Due Time", validators=[Optional()])
    desc = StringField("Description", widget=TextArea(),
                       validators=[Optional()])
