"""Routes for the application."""

from flask import render_template, flash, redirect, url_for, request, abort
from flask import jsonify, Response
from app import app, db, models
from flask_login import login_required, current_user, logout_user
import requests
from sqlalchemy import func, case, and_
from datetime import datetime, timezone, date, time
from random import sample
from decimal import Decimal, ROUND_HALF_UP
from .forms import WatchPartyForm, SearchForm, RatingForm, CommentForm
from .constants import USERNAME_REGEX, EMAIL_REGEX, PASSWORD_REGEX, headers
from .helpers import get_random_movies, validate_party
from .helpers import party_edit_allowed, party_check


@app.route("/", methods=["GET"])
def index():
    """Render the homepage."""
    if not current_user.is_authenticated:
        app.logger.info("User not authenticated")
        return render_template("welcome.html", title="Watch Parties",
                               movies=get_random_movies())

    search_form = SearchForm()
    form = WatchPartyForm()

    # Display the next Watch Party on the homepage
    next = (
        models.WatchParty.query
        .join(models.WatchPartyUser)
        .filter(
            models.WatchPartyUser.user_id == current_user.id,
            models.WatchParty.start_time >= datetime.now(timezone.utc),
            models.WatchParty.deleted_at.is_(None)
        )
        .order_by(models.WatchParty.start_time.asc())
        .first()
    )

    # Get next movie details
    if next:
        url = f"""https://api.themoviedb.org/3/movie/
            {next.movie_id}?language=en-US"""
        next_movie = requests.get(url, headers=headers).json()
        next_owner = models.User.query.filter(
            models.User.id == next.created_by).first()
    else:
        next_movie = None
        next_owner = None

    # Show all future public parties, ordered by start time and not deleted
    public = (
        models.WatchParty.query
        .filter(
            models.WatchParty.is_private.is_(False),
            models.WatchParty.start_time >= datetime.now(timezone.utc),
            models.WatchParty.deleted_at.is_(None)
        )
        .order_by(models.WatchParty.start_time.asc())
        .all()
    )

    # Display the user's username and profile colour in the navbaron all pages
    username = current_user.username
    colour = current_user.profile_colour

    app.logger.info(f"User {current_user.username} visited the homepage")
    return render_template("index.html", title="Home", next=next,
                           next_movie=next_movie, next_owner=next_owner,
                           public=public, form=form, search_form=search_form,
                           username=username, colour=colour)


@app.route("/parties", methods=["GET"])
@login_required
def parties():
    """Render the user's joined parties page."""
    # Get all upcoming and previous watch parties the user is in
    upcoming = (
        models.WatchPartyUser.query
        .join(models.WatchParty)
        .filter(
            models.WatchPartyUser.user_id == current_user.id,
            models.WatchParty.start_time >= datetime.now(timezone.utc),
            models.WatchParty.deleted_at.is_(None)
        )
        .order_by(models.WatchParty.start_time.asc())
        .all()
    )

    previous = models.WatchPartyUser.query.join(models.WatchParty).filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchParty.start_time < datetime.now(timezone.utc),
        models.WatchParty.deleted_at.is_(None)
    ).order_by(
        models.WatchParty.start_time.desc()
    ).all()

    username = current_user.username
    colour = current_user.profile_colour

    search_form = SearchForm()
    form = WatchPartyForm()

    app.logger.info(
        f"User {current_user.username} visited their joined parties page")
    return render_template("parties.html", title="Joined Parties",
                           upcoming=upcoming, previous=previous,
                           username=username, colour=colour,
                           search_form=search_form, form=form)


@app.route("/my-parties", methods=["GET"])
@login_required
def my_parties():
    """Render the user's created parties page."""
    # Get all upcoming and previous watch parties the user created
    upcoming = models.WatchPartyUser.query\
    .join(models.WatchParty, and_(
        models.WatchParty.id == models.WatchPartyUser.watch_party_id,
        models.WatchParty.created_by == models.WatchPartyUser.user_id
    ))\
    .filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchParty.start_time >= datetime.now(timezone.utc),
        models.WatchParty.deleted_at.is_(None)
    )\
    .order_by(
        models.WatchParty.start_time.asc()
    ).all()

    previous = models.WatchPartyUser.query\
    .join(models.WatchParty, and_(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchParty.id == models.WatchPartyUser.watch_party_id,
        models.WatchParty.created_by == models.WatchPartyUser.user_id
    ))\
    .filter(
        models.WatchParty.start_time < datetime.now(timezone.utc),
        models.WatchParty.deleted_at.is_(None)
    )\
    .order_by(
        models.WatchParty.start_time.desc()
    ).all()

    username = current_user.username
    colour = current_user.profile_colour

    search_form = SearchForm()
    form = WatchPartyForm()

    app.logger.info(
        f"User {current_user.username} visited their created parties page")
    return render_template("parties.html", title="My Parties",
                           upcoming=upcoming, previous=previous,
                           username=username, colour=colour,
                           search_form=search_form, form=form)


@app.route("/create", methods=["POST"])
@login_required
def create():
    """Handle creating a Watch Party."""
    form = WatchPartyForm()

    if form.validate_on_submit():
        # Validate the form
        result = validate_party(
            form.title.data,
            form.movie_id.data,
            form.description.data,
            form.location.data,
            form.start_date.data,
            form.start_time.data,
            form.is_private.data
        )

        if isinstance(result, str):
            flash("Could not create Watch Party. " + result)
            abort(404)

        wp = models.WatchParty(
            title=form.title.data,
            movie_id=form.movie_id.data,
            description=form.description.data,
            location=form.location.data,
            start_time=result,
            created_by=current_user.id,
            is_private=form.is_private.data
        )

        # Do not commit until we have added the user to the Watch Party
        db.session.add(wp)
        db.session.flush()

        wp_user = models.WatchPartyUser(
            user_id=current_user.id, watch_party_id=wp.id
        )

        db.session.add(wp_user)
        db.session.commit()

        app.logger.info(f"{current_user.username} created Watch Party {wp.id}")
        return redirect(url_for("party", url=wp.url))

    # If the form did't validate, flash an error and abort
    app.logger.debug(f"Invalid Watch Party form by {current_user.username}")
    flash("Could not create Watch Party. Invalid party data.")
    abort(404)


@app.route("/party/<url>", methods=["GET"])
@login_required
def party(url):
    """Render the Watch Party page."""
    wp = party_check(url)

    # Check if the user is the owner or a member of the Watch Party
    is_owner = models.WatchParty.query.filter(
        models.WatchParty.created_by == current_user.id,
        models.WatchParty.id == wp.id
    ).first() is not None

    is_member = False

    if not is_owner:
        is_member = models.WatchPartyUser.query.filter(
            models.WatchPartyUser.user_id == current_user.id,
            models.WatchPartyUser.watch_party_id == wp.id
        ).first() is not None

    # Get the owner and members of the Watch Party if not deleted
    owner = models.User.query.filter(models.User.id == wp.created_by).first()
    members = models.User.query.join(
        models.WatchPartyUser).filter(
            models.WatchPartyUser.watch_party_id == wp.id,
            models.User.deleted_at.is_(None),
            models.User.id != owner.id
    ).all()

    # Show the user's rating if they are in the Watch Party
    if is_owner or is_member:
        rating = models.WatchPartyUser.query.filter(
            models.WatchPartyUser.user_id == current_user.id,
            models.WatchPartyUser.watch_party_id == wp.id
        ).first().rating
    else:
        rating = None

    # Get the average rating of the Watch Party
    avg_rating = db.session.query(
        func.avg(models.WatchPartyUser.rating)).filter(
            models.WatchPartyUser.watch_party_id == wp.id
    ).scalar()

    # Because Python doesn't round properly for some reason
    if avg_rating:
        avg_rating = float(Decimal(avg_rating).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP))

    # Get movie details
    url = f"https://api.themoviedb.org/3/movie/{wp.movie_id}?language=en-US"
    movie = requests.get(url, headers=headers)

    # Get comments with user info and reaction counts in creation order
    comment_data = (
        db.session.query(
            models.Comment,
            models.User.username,
            models.User.profile_colour,
            # Count likes
            func.count(
                case((models.CommentReaction.is_like.is_(True), 1))
            ).label("likes"),
            # Count dislikes
            func.count(
                case((models.CommentReaction.is_like.is_(False), 1))
            ).label("dislikes"),
            # Check if current user has reacted
            func.max(
                case(
                    (models.CommentReaction.user_id == current_user.id,
                    models.CommentReaction.is_like)
                )
            ).label("user_reaction"),
            # Check if user can edit (is comment owner)
            (models.Comment.user_id == current_user.id).label("can_edit")
        )
        .join(
            models.User,
            models.Comment.user_id == models.User.id
        )
        .outerjoin(
            models.CommentReaction,
            models.Comment.id == models.CommentReaction.comment_id
        )
        .filter(models.Comment.watch_party_id == wp.id)
        .group_by(
            models.Comment.id,
            models.User.username,
            models.User.profile_colour
        )
        .all()
    )

    # Process the results into a format easy to use in templates
    comments = []
    for comment in comment_data:
        comments.append({
            "id": comment.Comment.id,
            "content": comment.Comment.content,
            "updated_at": comment.Comment.updated_at,
            "username": comment.username,
            "profile_colour": comment.profile_colour,
            "likes": comment.likes,
            "dislikes": comment.dislikes,
            "user_reaction": comment.user_reaction,
            "can_edit": comment.can_edit,
            "deleted_at": comment.Comment.deleted_at
        })

    form = WatchPartyForm()
    edit_form = WatchPartyForm(obj=wp)
    search_form = SearchForm()
    rating_form = RatingForm()
    comment_form = CommentForm()

    username = current_user.username
    colour = current_user.profile_colour

    app.logger.info(f"{current_user.username} visited Watch Party {wp.id}")
    return render_template(
        "party.html", title=f"{owner.username}'s Watch Party", wp=wp,
        owner=owner, is_owner=is_owner, is_member=is_member, members=members,
        movie=movie.json(), form=form, search_form=search_form,
        edit_form=edit_form, rating=rating, avg_rating=avg_rating,
        rating_form=rating_form, comment_form=comment_form, comments=comments,
        username=username, colour=colour)


@app.route("/party/join/<url>", methods=["POST"])
@login_required
def join_party(url):
    """Join a Watch Party."""
    wp = party_check(url)

    # Check user is not already in the Watch Party
    if models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id
    ).first():
        flash("You are already a member of this Watch Party", "warning")
        return redirect(url_for("party", url=wp.url))

    # Add user to Watch Party
    wp_user = models.WatchPartyUser(
        user_id=current_user.id, watch_party_id=wp.id)
    db.session.add(wp_user)
    db.session.commit()

    app.logger.info(f"{current_user.username} joined Watch Party {wp.id}")
    flash("You have joined the Watch Party", "success")
    return redirect(url_for("party", url=wp.url))


@app.route("/party/leave/<url>", methods=["POST"])
@login_required
def leave_party(url):
    """Leave a Watch Party."""
    wp = party_check(url)

    # Check user is not the owner
    if wp.created_by == current_user.id:
        app.logger.debug(
            f"""{current_user.username} tried to leave their own """
            """Watch Party, {wp.id}""")
        flash("You cannot leave a Watch Party you created", "warning")
        return redirect(url_for("party", url=wp.url))

    # Check user is in the Watch Party
    wp_user = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id
    ).first()

    if not wp_user:
        app.logger.debug(
            f"""{current_user.username} tried to leave a Watch Party """
            """they are not in, {wp.id}""")
        flash("You are not a member of this Watch Party")
        return redirect(url_for("party", url=wp.url))

    # Remove user from Watch Party
    db.session.delete(wp_user)
    db.session.commit()

    app.logger.info(f"{current_user.username} left Watch Party {wp.id}")
    flash("You have left the Watch Party")
    return redirect((url_for("party", url=wp.url)))


@app.route("/party/edit/<url>", methods=["POST"])
@login_required
def edit_party(url):
    """Edit a Watch Party."""
    wp = party_check(url)

    result = party_edit_allowed(wp)
    if isinstance(result, Response):
        return result

    form = WatchPartyForm()
    if form.validate_on_submit():
        result = validate_party(form.title.data, form.movie_id.data,
                                form.description.data, form.location.data,
                                form.start_date.data, form.start_time.data,
                                form.is_private.data)

        if isinstance(result, str):
            app.logger.debug(
                f"""Invalid Watch Party update form by """
                """{current_user.username} for {wp.id}""")
            flash("Could not update Watch Party. " + result)
            return redirect(url_for("party", url=wp.url))

        # Check if we are updating anything
        if (form.title.data == wp.title and
                form.movie_id.data == wp.movie_id and
                form.description.data == wp.description and
                form.location.data == wp.location and
                result == wp.start_time and
                form.is_private.data == wp.is_private):
            app.logger.debug(
                f"""No changes made to Watch Party {wp.id} by """
                """{current_user.username}""")
            flash("No changes made to the Watch Party", "warning")
            return redirect(url_for("party", url=wp.url))

        wp.title = form.title.data
        wp.movie_id = form.movie_id.data
        wp.description = form.description.data
        wp.location = form.location.data
        wp.start_time = datetime.combine(
            form.start_date.data, form.start_time.data)
        wp.is_private = form.is_private.data
        wp.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        app.logger.info(
            f"Watch Party {wp.id} updated by {current_user.username}")
        flash("Watch Party updated", "success")
        return redirect(url_for("party", url=wp.url))

    # If the form did't validate, flash an error
    app.logger.debug(
        f"""Invalid Watch Party update form by {current_user.username} """
        """for {wp.id}""")
    flash("Could not update Watch Party. Invalid party data")
    return redirect(url_for("party", url=wp.url))


@app.route("/party/delete/<url>", methods=["POST"])
@login_required
def delete_party(url):
    """Delete a Watch Party."""
    wp = party_check(url)

    result = party_edit_allowed(wp)
    if isinstance(result, Response):
        return result

    wp.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    app.logger.info(f"Watch Party {wp.id} deleted by {current_user.username}")
    flash("Watch Party deleted", "success")
    return redirect(url_for("index"))


@app.route("/party/rate/<url>", methods=["POST"])
@login_required
def rate(url):
    """Rate the Watch Party."""
    wp = party_check(url)

    # Require them to be in the Watch Party
    member = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id).first()
    if not member:
        app.logger.debug(
            f"""{current_user.username} tried to rate a Watch Party """
            """they are not in, {wp.id}""")
        return "you are not a member of this Watch Party", 403

    form = RatingForm()
    if form.validate_on_submit():
        # Require the rating to be an integer between 1 and 5
        try:
            new_rating = int(form.rating.data)
            if new_rating < 1 or new_rating > 5:
                raise ValueError
        except ValueError:
            app.logger.debug(
                f"""Invalid Watch Party rating form by """
                """{current_user.username} for {wp.id}""")
            return "Rating must be an integer between 1 and 5", 400

        member.rating = new_rating
        db.session.commit()

        app.logger.info(
            f"Watch Party {wp.id} rated by {current_user.username}")

        avg_rating = db.session.query(func.avg(
            models.WatchPartyUser.rating)).filter(
                models.WatchPartyUser.watch_party_id == wp.id
            ).scalar()

        avg_rating = float(Decimal(avg_rating).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP))

        return jsonify(
            {"status": "OK", "rating": new_rating, "avgRating": avg_rating}
            ), 200

    # If the form did't validate, return an error
    app.logger.debug(
        f"""Invalid Watch Party rating form by {current_user.username} """
        """for {wp.id}""")
    return "Invalid rating", 400


@app.route("/party/comment/<url>", methods=["POST"])
@login_required
def comment(url):
    """Comment in a Watch Party."""
    wp = party_check(url)

    # Require them to be in the Watch Party
    member = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id).first()
    if not member:
        app.logger.debug(
            f"""{current_user.username} tried to comment in a Watch Party """
            """they are not in, {wp.id}""")
        flash("you are not a member of this Watch Party", "warning")
        return redirect(url_for("party", url=wp.url))

    form = CommentForm()
    if form.validate_on_submit():
        if form.content.data.strip() == "":
            app.logger.debug(
                f"""Empty comment by {current_user.username} in Watch Party """
                """{wp.id}""")
            flash("Comment cannot be empty", "warning")
            return redirect(url_for("party", url=wp.url))

        if len(form.content.data.strip()) > 500:
            app.logger.debug(
                f"""Comment too long by {current_user.username} in """
                """Watch Party {wp.id}""")
            flash("Comment cannot be longer than 500 characters", "warning")
            return redirect(url_for("party", url=wp.url))

        comment = models.Comment(
            content=form.content.data.strip(),
            user_id=current_user.id,
            watch_party_id=wp.id
        )
        db.session.add(comment)
        db.session.commit()

        app.logger.info(
            f"Comment by {current_user.username} in Watch Party {wp.id}")
        return redirect(url_for("party", url=wp.url))

    # If the form did't validate, flash an error
    app.logger.debug(
        f"""Invalid comment form by {current_user.username} in Watch Party """
        """{wp.id}""")
    flash("Could not add comment. Invalid comment data", "warning")
    return redirect(url_for("party", url=wp.url))


@app.route("/party/vote/<url>/<id>", methods=["POST"])
@login_required
def vote(url, id):
    """React to a comment in a Watch Party."""
    wp = party_check(url)

    # Require them to be in the Watch Party
    member = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id).first()
    if not member:
        app.logger.debug(
            f"""{current_user.username} tried to react to a comment in a """
            """Watch Party they are not in, {wp.id}""")
        return "you are not a member of this Watch Party", 403

    # Require the comment to exist
    comment = models.Comment.query.filter(
        models.Comment.id == id,
        models.Comment.watch_party_id == wp.id
    ).first()

    if not comment:
        app.logger.debug(f"Comment does not exist in Watch Party {wp.id}")
        return "comment does not exist", 404

    # Require the comment to not be deleted
    if comment.deleted_at is not None:
        app.logger.debug(f"Comment has been deleted in Watch Party {wp.id}")
        return "comment has been deleted", 403

    new_reaction = request.get_json()
    try:
        new_reaction = new_reaction["voteType"] == "like"
    except KeyError:
        app.logger.debug(
            f"""Invalid reaction by {current_user.username} in Watch Party """
            """{wp.id}""")
        return "invalid reaction", 400

    reaction = models.CommentReaction.query.filter(
        models.CommentReaction.user_id == current_user.id,
        models.CommentReaction.comment_id == id).first()
    user_reaction = None

    # If the user has not reacted, create a new reaction
    if not reaction:
        reaction = models.CommentReaction(
            user_id=current_user.id,
            comment_id=id,
            is_like=new_reaction
        )
        db.session.add(reaction)
        user_reaction = new_reaction
    # If the user has reacted, update the reaction
    else:
        if reaction.is_like == new_reaction:
            db.session.delete(reaction)
        else:
            reaction.is_like = new_reaction
            user_reaction = new_reaction

    db.session.commit()
    app.logger.info(
        f"Reaction by {current_user.username} in Watch Party {wp.id}")

    # Return the updated reaction counts
    likes = (
        db.session.query(
            func.count(models.CommentReaction.is_like)
        )
        .filter(
            models.CommentReaction.comment_id == id,
            models.CommentReaction.is_like.is_(True)
        )
        .scalar()
    )

    dislikes = (
        db.session.query(
            func.count(models.CommentReaction.is_like)
        )
        .filter(
            models.CommentReaction.comment_id == id,
            models.CommentReaction.is_like.is_(False)
        )
        .scalar()
    )

    return jsonify({
        "status": "OK",
        "reaction": user_reaction,
        "likes": likes, "dislikes": dislikes
    }), 200


@app.route("/party/comment/edit/<url>/<id>", methods=["POST"])
@login_required
def edit_comment(url, id):
    """Edit a comment in a Watch Party."""
    wp = party_check(url)

    # Require them to be in the Watch Party
    member = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id).first()
    if not member:
        app.logger.debug(
            f"""{current_user.username} tried to edit a comment in a """
            """Watch Party they are not in, {wp.id}""")
        return "you are not a member of this Watch Party", 403

    # Require the comment to exist
    comment = models.Comment.query.filter(
        models.Comment.id == id,
        models.Comment.watch_party_id == wp.id
    ).first()

    if not comment:
        app.logger.debug(
            f"""{current_user.username} tried to edit a non-existent """
            """comment in Watch Party {wp.id}""")
        return "comment does not exist", 404

    # Require the comment to not be deleted
    if comment.deleted_at is not None:
        app.logger.debug(
            f"""{current_user.username} tried to edit a deleted comment """
            """in Watch Party {wp.id}""")
        return "comment has been deleted", 403

    # Require the user to be the owner of the comment
    if comment.user_id != current_user.id:
        app.logger.debug(
            f"""{current_user.username} tried to edit a comment they did """
            """not create in Watch Party {wp.id}""")
        return "you did not create this comment", 403

    response = request.get_json()
    try:
        new_content = response["content"]
    except KeyError:
        app.logger.debug(
            f"""Invalid comment edit by {current_user.username} in """
            """Watch Party {wp.id}""")
        return "invalid comment", 400

    new_content = new_content.strip()
    if new_content == "":
        app.logger.debug(
            f"""Empty comment edit by {current_user.username} in """
            """Watch Party {wp.id}""")
        return "comment cannot be empty", 400

    if len(new_content) > 500:
        app.logger.debug(
            f"""Comment too long by {current_user.username} in """
            """Watch Party {wp.id}""")
        return "comment cannot be longer than 500 characters", 400

    if new_content == comment.content:
        app.logger.debug(
            f"""No changes made to comment by {current_user.username} """
            """in Watch Party {wp.id}""")
        return jsonify({
            "status": "OK", "content": new_content,
            "updatedAt": comment.updated_at.strftime("%H:%M, %d/%m/%Y")
            }), 200

    comment.content = new_content
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    app.logger.info(
        f"Comment edited by {current_user.username} in Watch Party {wp.id}")
    return jsonify({
        "status": "OK", "content": new_content,
        "updatedAt": comment.updated_at.strftime("%H:%M, %d/%m/%Y")
        }), 200


@app.route("/party/comment/delete/<url>/<id>", methods=["POST"])
@login_required
def delete_comment(url, id):
    """Delete a comment in a Watch Party."""
    wp = party_check(url)

    # Require them to be in the Watch Party
    member = models.WatchPartyUser.query.filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchPartyUser.watch_party_id == wp.id).first()
    if not member:
        app.logger.debug(
            f"""{current_user.username} tried to delete a comment in a """
            """Watch Party they are not in, {wp.id}""")
        flash("you are not a member of this Watch Party", "warning")
        return redirect(url_for("party", url=wp.url))

    # Require the comment to exist
    comment = models.Comment.query.filter(
        models.Comment.id == id,
        models.Comment.watch_party_id == wp.id).first()

    if not comment:
        app.logger.debug(
            f"""{current_user.username} tried to delete a non-existent """
            """comment in Watch Party {wp.id}""")
        flash("comment does not exist", "warning")
        return redirect(url_for("party", url=wp.url))

    # Require the comment to not be deleted
    if comment.deleted_at is not None:
        app.logger.debug(
            f"""{current_user.username} tried to delete a deleted comment """
            """in Watch Party {wp.id}""")
        flash("comment has been deleted", "warning")
        return redirect(url_for("party", url=wp.url))

    # Require the user to be the owner of the comment
    if comment.user_id != current_user.id:
        app.logger.debug(
            f"""{current_user.username} tried to delete a comment they did """
            """not create in Watch Party {wp.id}""")
        flash("you did not create this comment", "warning")
        return redirect(url_for("party", url=wp.url))

    comment.deleted_at = datetime.now(timezone.utc)
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    app.logger.info(
        f"Comment deleted by {current_user.username} in Watch Party {wp.id}")
    return redirect(url_for("party", url=wp.url))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Render the user profile page."""
    if current_user.deleted_at is not None:
        flash("Your account has been deleted", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        response = request.get_json()

        # Validate the response
        if "edit-username" in response:
            new_username = response["edit-username"]

            if not isinstance(new_username, str):
                app.logger.debug(
                    f"Wrong type for username by {current_user.username}")
                return "Invalid username", 400

            if new_username.strip() == "":
                app.logger.debug(f"Empty username by {current_user.username}")
                return "Username cannot be empty", 400

            if len(new_username) > 30:
                app.logger.debug(
                    f"Username too long by {current_user.username}")
                return "Username cannot be longer than 50 characters", 400

            if new_username == current_user.username:
                app.logger.debug(
                    f"""Username same as current username by """
                    """{current_user.username}""")
                return (
                    "Username cannot be the same as the current username", 400)

            if not USERNAME_REGEX.match(new_username):
                app.logger.debug(
                    f"Invalid username by {current_user.username}")
                return "Username is invalid", 400

            username = models.User.query.filter(
                models.User.username == new_username).first()
            if username:
                app.logger.debug(
                    f"Username already taken by {current_user.username}")
                return "Username already taken", 400

            app.logger.info(
                f""""{current_user.username} changed their username to """
                """{new_username}""")
            current_user.username = new_username
            db.session.commit()

            return jsonify({"status": "OK", "value": new_username}), 200
        elif "edit-email" in response:
            new_email = response["edit-email"]

            if new_email.strip() == "":
                app.logger.debug(f"Empty email by {current_user.username}")
                return "Email cannot be empty", 400

            if len(new_email) > 256:
                app.logger.debug(f"Email too long by {current_user.username}")
                return "Email cannot be longer than 256 characters", 400

            if not EMAIL_REGEX.match(new_email):
                app.logger.debug(f"Invalid email by {current_user.username}")
                return "Email is invalid", 400

            if new_email == current_user.email:
                app.logger.debug(
                    f"Email same as current email by {current_user.username}")
                return "Email cannot be the same as the current email", 400

            email = models.User.query.filter(
                models.User.email == new_email,
                models.User.deleted_at.is_(None)).first()
            if email:
                app.logger.debug(
                    f"""{current_user.username}'s Email was already taken """
                    """by {email.username}""")
                return "Email already taken", 400

            app.logger.info(
                f"""{current_user.username} changed their email from """
                """{current_user.email} to {new_email}""")
            current_user.email = new_email
            db.session.commit()

            return jsonify({"status": "OK", "value": new_email}), 200
        elif "edit-password" in response:
            new_password = response["edit-password"]

            if "edit-password-confirm" not in response:
                app.logger.debug(
                    f"""Password confirmation required by """
                    """{current_user.username}""")
                return "Password confirmation required", 400

            new_confirm = response["edit-password-confirm"]

            if new_password.strip() == "":
                app.logger.debug(f"Empty password by {current_user.username}")
                return "Password cannot be empty", 400

            if len(new_password) < 8 or len(new_password) > 24:
                app.logger.debug(
                    f"Password length invalid by {current_user.username}")
                return "Password must be between 8 and 24 characters", 400

            if not PASSWORD_REGEX.match(new_password):
                app.logger.debug(
                    f"Password invalid by {current_user.username}")
                return "Password is invalid", 400

            if new_password != new_confirm:
                app.logger.debug(
                    f"Passwords do not match by {current_user.username}")
                return "Passwords do not match", 400

            app.logger.info(f"{current_user.username} changed their password")
            current_user.set_password(new_password)
            db.session.commit()

            return jsonify({"status": "OK"}), 200
        elif "edit-colour" in response:
            new_colour = response["edit-colour"]

            if new_colour not in models.PROFILE_COLOURS:
                app.logger.debug(f"Invalid colour by {current_user.username}")
                return "Invalid colour", 400

            app.logger.info(
                f"""{current_user.username} changed their profile colour """
                """from {current_user.profile_colour} to {new_colour}""")
            current_user.profile_colour = new_colour
            db.session.commit()

            return jsonify({"status": "OK", "value": new_colour}), 200
        elif "delete-profile" in response:
            current_user.deleted_at = datetime.now(timezone.utc)
            db.session.commit()
            app.logger.info(f"{current_user.username} deleted their account")

            logout_user()
            flash("Your account has been deleted", "success")
            return jsonify({"status": "OK"}), 200
        else:
            app.logger.debug(
                f"Invalid profile edit request by {current_user.username}")
            return "Invalid request", 400

    user = models.User.query.filter(models.User.id == current_user.id).first()

    username = current_user.username
    colour = current_user.profile_colour

    search_form = SearchForm()
    form = WatchPartyForm()

    return render_template(
        "profile.html", title="Profile", user=user,
        colours=models.PROFILE_COLOURS, username=username, colour=colour,
        search_form=search_form, form=form)


@app.route("/query", methods=["POST"])
@login_required
def query():
    """Query the TMDB API and return the results."""
    search = request.get_json()["search"].strip()

    url = "https://api.themoviedb.org/3/search/movie?"
    url += f"query={search}&include_adult=false&language=en-US&page=1"

    response = requests.get(url, headers=headers)
    return response.text


@app.errorhandler(404)
def page_not_found(e):
    """Render the 404 page."""
    return render_template("404.html"), 404
