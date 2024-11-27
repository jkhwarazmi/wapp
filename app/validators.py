"""Validates Flask form inputs, flashes errors and redirects as appropriate."""

from datetime import date, datetime, time
from flask import flash, redirect, url_for


def validate_form_fields(module, title, due_date, due_time, desc):
    """Validate all form fields."""
    # Validate module length (1-10 characters)
    module_valid = 0 < len(module) <= 10

    # Validate title length (1-50 characters)
    title_valid = 0 < len(title) <= 50

    # Validate due date is a date object and between 01/09/2023 and 01/09/2027
    due_date_valid = isinstance(due_date, date)
    if due_date_valid:
        start_date = datetime.strptime("2023-09-01", "%Y-%m-%d").date()
        end_date = datetime.strptime("2027-09-01", "%Y-%m-%d").date()
        due_date_valid = start_date <= due_date <= end_date

    # Validate due time is a time object if provided
    due_time_valid = isinstance(due_time, time) if due_time else True

    # Validate description length (optional, max 500 characters)
    desc_valid = len(desc) <= 500 if desc else True

    # Store error messages
    errors = {}
    if not module_valid:
        errors["module"] = (
            "Invalid module name. Please enter up to 10 characters."
        )
    if not title_valid:
        errors["title"] = (
            "Invalid assessment title. Please enter up to 50 characters."
        )
    if not due_date_valid:
        errors["due_date"] = (
            "Invalid due date. "
            "Please enter a date between 01/09/2023 and 01/09/2027 "
            "in the format dd/mm/yyyy."
        )
    if not due_time_valid:
        errors["due_time"] = (
            "Invalid due time. "
            "Optionally, enter the time in 24-hour format: HH:MM."
        )
    if not desc_valid:
        errors["desc"] = (
            "Invalid description. Optionally enter up to 500 characters."
        )

    return errors


def handle_validation_errors(errors, id=None):
    """Flash error messages and redirect based on validation results."""
    for field, message in errors.items():
        flash(message, "danger")
    if id:
        return redirect(url_for("edit", id=id))
    return redirect(url_for("add"))
