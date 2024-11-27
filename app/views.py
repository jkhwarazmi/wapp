"""Routes for the application."""

from flask import render_template, flash, redirect, url_for, request
from app import app, db, models
from datetime import datetime, timezone
from .forms import AssessmentForm
from .validators import validate_form_fields, handle_validation_errors


@app.route("/")
def index():
    """Render the index page."""
    # Order complete assessments by completion date
    complete = db.session.query(models.Assessment).filter(
        models.Assessment.completed_at.isnot(None),
        models.Assessment.deleted_at.is_(None)
    ).order_by(
        models.Assessment.completed_at.desc()
    ).all()

    # Order incomplete assessments by due date and time
    incomplete = db.session.query(models.Assessment).filter(
        models.Assessment.completed_at.is_(None),
        models.Assessment.deleted_at.is_(None)
    ).order_by(
        models.Assessment.due_date.asc(),
        models.Assessment.due_time.asc()
    ).all()

    # Order deleted assessments by deletion date
    deleted = db.session.query(models.Assessment).filter(
        models.Assessment.deleted_at.isnot(None)
    ).order_by(
        models.Assessment.deleted_at.desc()
    ).all()

    return render_template("index.html", title="Assessment List",
                           complete=complete, incomplete=incomplete,
                           deleted=deleted)


@app.route("/add", methods=["GET", "POST"])
def add():
    """Render the add page and handle adding assessments."""
    deleted = db.session.query(models.Assessment).filter(
        models.Assessment.deleted_at.isnot(None)
    ).order_by(
        models.Assessment.deleted_at.desc()
    ).all()

    form = AssessmentForm()

    if form.validate_on_submit():
        a = models.Assessment(
            module=form.module.data,
            title=form.title.data,
            due_date=form.due_date.data,
            due_time=form.due_time.data,
            desc=form.desc.data
        )

        # Validate all fields
        errors = validate_form_fields(a.module, a.title, a.due_date,
                                      a.due_time, a.desc)
        if errors:
            return handle_validation_errors(errors)

        # Check if the assessment has same name and title as another
        matching = db.session.query(models.Assessment).filter(
            models.Assessment.module.ilike(a.module),
            models.Assessment.title.ilike(a.title),
        ).first()

        if matching:
            if matching.deleted_at is not None:
                flash(
                    "Deleted assessment with the same module and title already"
                    " exists, please restore it instead.", "warning"
                )
                return redirect(url_for("deleted"))
            else:
                flash(
                    "Assessment with the same module and title already exists."
                    " Your assessment has not been added.", "warning"
                )
                return redirect(url_for("add"))

        db.session.add(a)
        db.session.commit()

        flash("Assessment added succesfully.", "success")
        return redirect(url_for("add"))
    return render_template("add.html", title="Add Assessment",
                           form=form, deleted=deleted)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    """Render the edit page and handle editing assessments."""
    try:
        # Check if the assessment exists
        message = "No assessment found."
        a = db.session.get(models.Assessment, id)

        # Raise error if it exists but is deleted
        if a.deleted_at is not None:
            message = "Deleted assessments cannot be edited " \
                "without restoring them first."
            raise Exception()
    except Exception:
        flash(message, "warning")
        return redirect(url_for("index"))

    deleted = db.session.query(models.Assessment).filter(
        models.Assessment.deleted_at.isnot(None)
    ).order_by(
        models.Assessment.deleted_at.desc()
    ).all()

    form = AssessmentForm(obj=a)

    if form.validate_on_submit():
        # Validate all fields
        errors = validate_form_fields(form.module.data, form.title.data,
                                      form.due_date.data, form.due_time.data,
                                      form.desc.data)
        if errors:
            return handle_validation_errors(errors, id=id)

        # Check if the assessment has same name and title as another
        matching = db.session.query(models.Assessment).filter(
            models.Assessment.module.ilike(form.module.data),
            models.Assessment.title.ilike(form.title.data),
        ).first()

        # Check if the matching assessment is not the current one
        if matching and matching.id != a.id:
            if matching.deleted_at is not None:
                flash(
                    "Deleted assessment with the same module and title already"
                    " exists, please restore it instead.", "warning")
                return redirect(url_for("deleted"))
            else:
                flash(
                    "Assessment with the same module and title already exists."
                    "Your changes have not been saved.", "warning")
                return redirect(url_for("edit", id=id))

        a.module = form.module.data
        a.title = form.title.data
        a.due_date = form.due_date.data
        a.due_time = form.due_time.data
        a.desc = form.desc.data

        db.session.commit()

        flash("Assessment edited succesfully.", "success")
        return redirect(url_for("index"))
    return render_template("edit.html", title="Edit Assessment", form=form,
                           assessment=a, deleted=deleted)


@app.route("/complete", methods=["POST"])
def complete():
    """Mark an assessment as complete."""
    try:
        # Attempt to find the assessment
        message = "No assessment found."
        id = request.form.get("id")
        a = db.session.get(models.Assessment, id)

        # Cannot complete an already completed assessment or a deleted one
        if a.completed_at is not None:
            message = "Assessment has already been completed."
            raise Exception()
        if a.deleted_at is not None:
            message = "Deleted assessments cannot be completed " \
                "without restoring them first"
            raise Exception()
    except Exception:
        flash(message, "warning")
        return redirect(url_for("index"))

    a.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Assessment marked as complete.", "success")
    return redirect(url_for("index"))


@app.route("/restore", methods=["POST"])
def restore():
    """Restore deleted assessments or mark completed ones as incomplete."""
    try:
        # Initially assume we are trying to restore a completed assessment
        message = "No assessment found."
        id = request.form.get("id")
        a = db.session.get(models.Assessment, id)

        # Cannot mark an incomplete assessment as incomplete
        if a.completed_at is None:
            message = "The assessment is already incomplete."
            raise Exception()
    except Exception:
        try:
            # Assume we are un-deleting assessments
            message = "No valid assessments to be deleted."
            restored = 0

            for i in request.form.getlist("remove-item"):
                message = "Attempted to restore an invalid assessment."

                # Check if the assessment exists and is deleted
                a = db.session.get(models.Assessment, i)
                if a.deleted_at is None:
                    message = "Cannot restore a non-deleted assessment."
                    raise Exception()

                # Restore the assessment
                a.deleted_at = None
                restored += 1
        except Exception:
            # Undo any changes made to the database
            db.session.rollback()
            restored = 0
            flash(message, "warning")
            redirect(url_for("deleted"))

        db.session.commit()
        if restored > 0:
            flash(
                f"{restored} assessment{'s' if restored > 1 else ''} "
                "restored succesfully.", "success"
            )
            return redirect(url_for("index"))

        flash(message, "warning")
        return redirect(url_for("index"))

    # Mark the completed assessment as incomplete
    a.completed_at = None
    db.session.commit()

    flash("Assessment marked as incomplete.", "success")
    return redirect(url_for("index"))


@app.route("/delete", methods=["POST"])
def delete():
    """Delete assessments."""
    try:
        message = "No assessment found."
        id = request.form.get("id")
        a = db.session.get(models.Assessment, id)

        if a.deleted_at is not None:
            message = "Assessment has already been deleted"
            raise Exception()
    except Exception:
        flash(message, "warning")
        return redirect(url_for("index"))

    a.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Assessment deleted.", "success")
    return redirect(url_for("index"))


@app.route("/deleted", methods=["GET", "POST"])
def deleted():
    """Render the deleted page and remove deleted assessments from the DB."""
    if request.method == "POST":
        try:
            message = "No valid assessments to be deleted."
            removed = 0

            for i in request.form.getlist("remove-item"):
                message = "Attempted to remove an invalid assessment."
                a = db.session.get(models.Assessment, i)

                # We can only remove deleted assessments
                if a.deleted_at is None:
                    message = "Cannot delete a non-deleted assessment."
                    raise Exception()

                db.session.delete(a)
                removed += 1
        except Exception:
            # If any assessment proves to be invalid, undo all changes
            db.session.rollback()
            removed = 0
            flash(message, "warning")
            redirect(url_for("deleted"))

        db.session.commit()
        if removed > 0:
            flash(
                f"{removed} assessment{'s' if removed > 1 else ''} "
                "deleted succesfully.", "success"
            )
            return redirect(url_for("deleted"))

    deleted = db.session.query(models.Assessment).filter(
        models.Assessment.deleted_at.isnot(None)
    ).order_by(
        models.Assessment.deleted_at.desc()
    ).all()

    if len(deleted) == 0:
        flash("There are no deleted assessments.", "info")
        return redirect(url_for("index"))

    return render_template("deleted.html", title="Deleted Assessments",
                           deleted=deleted)


@app.errorhandler(404)
def page_not_found(e):
    """Render the 404 page."""
    return render_template("404.html"), 404
