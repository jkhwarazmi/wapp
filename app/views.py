"""Routes for the application."""

from flask import render_template, flash, redirect, url_for, request, abort, jsonify, session
from app import app, db, models
from flask_login import login_required, current_user, logout_user
import requests
from sqlalchemy import func, case
from datetime import datetime, timezone
from random import sample
import re
import logging
from .forms import WatchPartyForm, SearchForm, RatingForm, CommentForm

TMDB_KEY = app.config["TMDB_KEY"]
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_KEY}"
}

username_regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]{0,29}$")
email_regex = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$")
password_regex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])[A-Za-z\d\W_]{8,24}$")

@app.route("/", methods=["GET"])
def index():
    """Render the homepage."""
    if not current_user.is_authenticated:
        # Get random recent movies
        current_year = datetime.now().year

        url = f"https://api.themoviedb.org/3/discover/movie"
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

        return render_template("welcome.html", title="Watch Parties", movies=movies)
    
    search_form = SearchForm()
    form = WatchPartyForm()

    # Index only shows next watch party and public watch parties
    # Button to create a new watch party in the navbar
    # Also option to see my watch parties in the navbar

    # Display the next watch party on the homepage
    next = models.WatchParty.query.join(models.WatchPartyUser).filter(
        models.WatchPartyUser.user_id == current_user.id,
        models.WatchParty.start_time >= datetime.now(timezone.utc),
        models.WatchParty.deleted_at == None
    ).order_by(models.WatchParty.start_time.asc()).first()
    
    # Get movie details
    if next:
        url = f"https://api.themoviedb.org/3/movie/{next.movie_id}?language=en-US"
        next_movie = requests.get(url, headers=headers).json()
        next_owner = models.User.query.filter(models.User.id == next.created_by).first()
    else:
        next_movie = None
        next_owner = None

    # Get all public watch parties, ordered by start time and not deleted and not in the past
    # May need to apply this logic to other queries as well
    public = (models.WatchParty.query
          .filter(
              models.WatchParty.is_private == False,
              models.WatchParty.start_time >= datetime.now(timezone.utc),
              models.WatchParty.deleted_at == None
          )
          .order_by(models.WatchParty.start_time.asc())
          .all())
    # Do we want the titles/posters for all of these as well??? PROBABLY, YES
    # Maybe TMDB queries should have their own function and .py file

    username=current_user.username
    colour=current_user.profile_colour

    return render_template("index.html", title="Home", next=next, next_movie=next_movie, next_owner=next_owner, public=public, form=form, search_form=search_form, username=username, colour=colour)


@app.route("/parties", methods=["GET"])
@login_required
def parties():
    """Render the user parties page."""
    upcoming = models.WatchPartyUser.query.join(models.WatchParty).filter(models.WatchPartyUser.user_id == current_user.id, models.WatchParty.start_time >= datetime.now(timezone.utc), models.WatchParty.deleted_at == None).order_by(models.WatchParty.start_time.asc()).all()
    previous = models.WatchPartyUser.query.join(models.WatchParty).filter(models.WatchPartyUser.user_id == current_user.id, models.WatchParty.start_time < datetime.now(timezone.utc), models.WatchParty.deleted_at == None).order_by(models.WatchParty.start_time.desc()).all()

    username=current_user.username
    colour=current_user.profile_colour

    search_form = SearchForm()
    form = WatchPartyForm()

    return render_template("parties.html", title="My Parties", upcoming=upcoming, previous=previous, username=username, colour=colour, search_form=search_form, form=form)


@app.route("/create", methods=["POST"])
@login_required
def create():
    """Handle creating a watch party."""
    form = WatchPartyForm()
    
    # If fail to create, i.e. invalid date, just send an AJAX response back to the client which we render
    # As an alert on the page
    error = ""

    if form.validate_on_submit():
        # Can a person make 2 watch parties at the same time? Sure, why not
        # Convert start_time and start_date to datetime object
        # Start time MUST be in the future, proper validation etc.

        if form.title.data.strip() == "":
            error = "Title cannot be empty."
        elif len(form.title.data) > 100:
            error = "Title cannot be longer than 100 characters."
        elif form.movie_id.data == None:
            error = "Invalid movie ID."
        elif form.description.data and len(form.description.data) > 500:
            error = "Description cannot be longer than 500 characters."
        elif form.location.data and len(form.location.data) > 100:
            error = "Location cannot be longer than 100 characters."
        elif form.start_date.data < datetime.now().date():
            error = "Start date cannot be in the past."
        elif form.start_date.data > datetime.now().date().replace(year=datetime.now().year+1):
            error = "Start date cannot be more than a year in the future."
        elif form.start_date.data == datetime.now().date() and form.start_time.data < datetime.now().time():
            error = "Start date cannot be in the past."
        
        wp = models.WatchParty(
            title=form.title.data,
            movie_id=form.movie_id.data,
            description=form.description.data,
            location=form.location.data,
            start_time=datetime.combine(form.start_date.data, form.start_time.data),
            created_by=current_user.id,
            is_private=form.is_private.data
        )

        # Do not commit until we have added the user to the watch party
        db.session.add(wp)
        db.session.flush()

        wp_user = models.WatchPartyUser(user_id=current_user.id, watch_party_id=wp.id)

        db.session.add(wp_user)
        db.session.commit()

        return redirect(url_for("party", url=wp.url))

    # Give full error page or something
    flash("Could not create watch party. " + error)
    abort(404)

@app.route("/party/<url>", methods=["GET"])
@login_required
def party(url):
    """Render the watch party page."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    if not wp:
       abort(404)
    elif wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    owner = models.User.query.filter(models.User.id == wp.created_by).first()
    is_owner = models.WatchParty.query.filter(models.WatchParty.created_by == current_user.id, models.WatchParty.id == wp.id).first() != None
    is_member = False

    if not is_owner:
        is_member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first() != None
    # Get all members of the watch party that aren't deleted and aren't the owner
    members = models.User.query.join(models.WatchPartyUser).filter(models.WatchPartyUser.watch_party_id == wp.id, models.User.deleted_at == None, models.User.id != owner.id).all()

    # Get movie details
    url = f"https://api.themoviedb.org/3/movie/{wp.movie_id}?language=en-US"

    # Editing functionality only on the same page and opens up same menu used to create the watch party so add the form back and give it default values on page load
    # Delete loads modal that confirms and then deletes the watch party only if the current user is the creator
    # Both EXPLICITLY CHECK IF THE USER IS THE OWNER OF THE WATCH PARTY

    # ALLOW RATING WP
    if is_owner or is_member:
        rating = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first().rating
    else:
        rating = None

    avg_rating = db.session.query(func.avg(models.WatchPartyUser.rating)).filter(models.WatchPartyUser.watch_party_id == wp.id).scalar()    

    movie = requests.get(url, headers=headers)

    # Get comments with user info and reaction counts
    # Don't order by updated_at to keep creation order
    comment_data = (
        db.session.query(
            models.Comment,
            models.User.username,
            models.User.profile_colour,
            # Count likes
            func.count(case((models.CommentReaction.is_like == True, 1))).label("likes"),
            # Count dislikes
            func.count(case((models.CommentReaction.is_like == False, 1))).label("dislikes"),
            # Check if current user has reacted
            func.max(case((models.CommentReaction.user_id == current_user.id, models.CommentReaction.is_like))).label("user_reaction"),
            # Check if user can edit (is comment owner)
            (models.Comment.user_id == current_user.id).label("can_edit")
        )
        .join(models.User, models.Comment.user_id == models.User.id)
        .outerjoin(models.CommentReaction, models.Comment.id == models.CommentReaction.comment_id)
        .filter(models.Comment.watch_party_id == wp.id)
        .group_by(models.Comment.id, models.User.username, models.User.profile_colour)
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

    username=current_user.username
    colour=current_user.profile_colour

    return render_template("party.html", title=f"{owner.username}'s Watch Party", wp=wp, owner=owner, is_owner=is_owner, is_member=is_member, members=members, movie=movie.json(), form=form, search_form=search_form, edit_form=edit_form, rating=rating, avg_rating=avg_rating, rating_form=rating_form, comment_form=comment_form, comments=comments, username=username, colour=colour) 

@app.route("/party/join/<url>", methods=["POST"])
@login_required
def join_party(url):
    """Join a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Check the party is not deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        return redirect(url_for("index"))

    # Check user is not already in the watch party
    if models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first():
        flash("You are already a member of this watch party", "warning")
        return redirect(url_for("party", url=wp.url))
    
    # Add user to watch party
    wp_user = models.WatchPartyUser(user_id=current_user.id, watch_party_id=wp.id)
    db.session.add(wp_user)
    db.session.commit()
    
    flash("You have joined the watch party", "success")
    return redirect(url_for("party", url=wp.url))

@app.route("/party/leave/<url>", methods=["POST"])
@login_required
def leave_party(url):
    """Leave a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Check the party is not deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        return redirect(url_for("index"))
    
    # Check user is not the owner
    if wp.created_by == current_user.id:
        flash("You cannot leave a watch party you created", "warning")
        return redirect(url_for("party", url=wp.url))

    # Check user is in the watch party
    wp_user = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    if not wp_user:
        flash("You are not a member of this watch party")
        return redirect(url_for("party", url=wp.url))

    # Remove user from watch party
    db.session.delete(wp_user)
    db.session.commit()

    flash("You have left the watch party")
    return redirect((url_for("party", url=wp.url)))

@app.route("/party/edit/<url>", methods=["POST"])
@login_required
def edit_party(url):
    """Edit a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    if not wp:
        abort(404)

    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)
    
    if wp.created_by != current_user.id:
        flash("You are not the owner of this watch party", "warning")
        return redirect(url_for("party", url=wp.url))

    if wp.start_time < datetime.now():
        flash("You cannot edit a watch party that has already started", "warning")
        return redirect(url_for("party", url=wp.url))
    

    form = WatchPartyForm()
    if form.validate_on_submit():
        # Can a person make 2 watch parties at the same time? Sure, why not
        # Convert start_time and start_date to datetime object
        # Start time MUST be in the future, proper validation etc.
        # Cannot update watch party if it has already started

        wp.title = form.title.data
        wp.movie_id = form.movie_id.data
        wp.description = form.description.data
        wp.location = form.location.data
        wp.start_time = datetime.combine(form.start_date.data, form.start_time.data)
        wp.is_private = form.is_private.data
        wp.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        flash("Watch party updated", "success")

    return redirect(url_for("party", url=wp.url))

@app.route("/party/delete/<url>", methods=["POST"])
@login_required
def delete_party(url):
    """Delete a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    if not wp:
        abort(404)

    if wp.deleted_at != None:
        flash("This watch party has already been deleted")
        abort(404)
    
    if wp.created_by != current_user.id:
        flash("You are not the owner of this watch party", "warning")
        return redirect(url_for("party", url=wp.url))
    
    if wp.start_time < datetime.now():
        flash("You cannot delete a watch party that has already started", "warning")
        return redirect(url_for("party", url=wp.url))
    
    wp.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Watch party deleted", "success")
    return redirect(url_for("index"))

@app.route("/party/rate/<url>", methods=["POST"])
@login_required
def rate(url):
    """Rate the watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Require the watch party to exist
    if not wp:
        abort(404)

    # Require the watch party to not be deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    # Require them to be in the watch party
    if not member:
        return "you are not a member of this watch party", 403

    form = RatingForm()
    if form.validate_on_submit():
        # Require the rating to be an integer between 1 and 5
        try:
            new_rating = int(form.rating.data)
            if new_rating < 1 or new_rating > 5:
                raise ValueError
        except ValueError:
            return "Rating must be an integer between 1 and 5", 400

        member.rating = new_rating
        db.session.commit()

        avg_rating = db.session.query(func.avg(models.WatchPartyUser.rating)).filter(models.WatchPartyUser.watch_party_id == wp.id).scalar()
        return jsonify({"status": "OK", "rating": new_rating, "avgRating": avg_rating}), 200 
    

@app.route("/party/comment/<url>", methods=["POST"])
@login_required
def comment(url):
    """Comment in a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Require the watch party to exist
    if not wp:
        abort(404)

    # Require the watch party to not be deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    # Require them to be in the watch party
    if not member:
        flash("you are not a member of this watch party", "warning")
        return redirect(url_for("party", url=wp.url))

    form = CommentForm()
    if form.validate_on_submit():
        if form.content.data.strip() == "":
            flash("Comment cannot be empty", "warning")
            return redirect(url_for("party", url=wp.url))
        elif len(form.content.data.strip()) > 500:
            flash("Comment cannot be longer than 500 characters", "warning")
            return redirect(url_for("party", url=wp.url))
        
        comment = models.Comment(
            content=form.content.data.strip(),
            user_id=current_user.id,
            watch_party_id=wp.id
        )
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for("party", url=wp.url))
    
@app.route("/party/vote/<url>/<id>", methods=["POST"])
@login_required
def vote(url, id):
    """React to a comment in a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Require the watch party to exist
    if not wp:
        abort(404)

    # Require the watch party to not be deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    # Require them to be in the watch party
    if not member:
        return "you are not a member of this watch party", 403
    
    # Require the comment to exist
    comment = models.Comment.query.filter(models.Comment.id == id, models.Comment.watch_party_id == wp.id).first()

    if not comment:
        return "comment does not exist", 404

    # Require the comment to not be deleted
    if comment.deleted_at != None:
        return "comment has been deleted", 403

    new_reaction = request.get_json()

    try:
        new_reaction = new_reaction["voteType"] == "like"
    except KeyError:
        return "invalid reaction", 400

    reaction = models.CommentReaction.query.filter(models.CommentReaction.user_id == current_user.id, models.CommentReaction.comment_id == id).first()
    user_reaction = None

    if not reaction:
        reaction = models.CommentReaction(
            user_id=current_user.id,
            comment_id=id,
            is_like=new_reaction
        )
        db.session.add(reaction)
        user_reaction = new_reaction
    else:
        if reaction.is_like == new_reaction:
            db.session.delete(reaction)
        else:
            reaction.is_like = new_reaction
            user_reaction = new_reaction

    db.session.commit()

    likes = db.session.query(func.count(models.CommentReaction.is_like)).filter(models.CommentReaction.comment_id == id, models.CommentReaction.is_like == True).scalar()
    dislikes = db.session.query(func.count(models.CommentReaction.is_like)).filter(models.CommentReaction.comment_id == id, models.CommentReaction.is_like == False).scalar()

    return jsonify({"status": "OK", "reaction": user_reaction, "likes": likes, "dislikes": dislikes}), 200


@app.route("/party/comment/edit/<url>/<id>", methods=["POST"])
@login_required
def edit_comment(url, id):
    """Edit a comment in a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Require the watch party to exist
    if not wp:
        abort(404)

    # Require the watch party to not be deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    # Require them to be in the watch party
    if not member:
        return "you are not a member of this watch party", 403
    
    # Require the comment to exist
    comment = models.Comment.query.filter(models.Comment.id == id, models.Comment.watch_party_id == wp.id).first()

    if not comment:
        return "comment does not exist", 404
    
    # Require the comment to not be deleted
    if comment.deleted_at != None:
        return "comment has been deleted", 403
    
    # Require the user to be the owner of the comment
    if comment.user_id != current_user.id:
        return "you did not create this comment", 403
    
    response = request.get_json()
    
    try:
        new_content = response["content"]
    except KeyError:
        return "invalid comment", 400
    
    new_content = new_content.strip()

    if new_content == "":
        return "comment cannot be empty", 400
    
    if len(new_content) > 500:
        return "comment cannot be longer than 500 characters", 400
    
    if new_content == comment.content:
        return jsonify({"status": "OK", "content": new_content, "updatedAt": comment.updated_at.strftime("%H:%M, %d/%m/%Y") }), 200

    comment.content = new_content
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"status": "OK", "content": new_content, "updatedAt": comment.updated_at.strftime("%H:%M, %d/%m/%Y") }), 200

@app.route("/party/comment/delete/<url>/<id>", methods=["POST"])
@login_required
def delete_comment(url, id):
    """Delete a comment in a watch party."""
    wp = models.WatchParty.query.filter(models.WatchParty.url == url).first()

    # Require the watch party to exist
    if not wp:
        abort(404)

    # Require the watch party to not be deleted
    if wp.deleted_at != None:
        flash("This watch party has been deleted")
        abort(404)

    member = models.WatchPartyUser.query.filter(models.WatchPartyUser.user_id == current_user.id, models.WatchPartyUser.watch_party_id == wp.id).first()

    # Require them to be in the watch party
    if not member:
        flash("you are not a member of this watch party", "warning")
        return redirect(url_for("party", url=wp.url))
    
    # Require the comment to exist
    comment = models.Comment.query.filter(models.Comment.id == id, models.Comment.watch_party_id == wp.id).first()

    if not comment:
        flash("comment does not exist", "warning")
        return redirect(url_for("party", url=wp.url))   
    
    # Require the comment to not be deleted
    if comment.deleted_at != None:
        flash("comment has been deleted", "warning")
        return redirect(url_for("party", url=wp.url))
    
    # Require the user to be the owner of the comment
    if comment.user_id != current_user.id:
        flash("you did not create this comment", "warning")
        return redirect(url_for("party", url=wp.url))

    comment.deleted_at = datetime.now(timezone.utc)
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return redirect(url_for("party", url=wp.url))



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Render the user profile page."""
    if current_user.deleted_at != None:
        flash("Your account has been deleted", "warning")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        response = request.get_json()

        if "edit-username" in response:
            new_username = response["edit-username"]

            if new_username.strip() == "":
                return "Username cannot be empty", 400
            elif len(new_username) > 30:
                return "Username cannot be longer than 50 characters", 400
            
            if new_username == current_user.username:
                return "Username cannot be the same as the current username", 400
            
            if not username_regex.match(new_username):
                return "Username is invalid", 400

            username = models.User.query.filter(models.User.username == new_username).first()

            if username:
                return "Username already taken", 400
            
            current_user.username = new_username
            db.session.commit()

            return jsonify({"status": "OK", "value": new_username}), 200
        elif "edit-email" in response:
            new_email = response["edit-email"]

            if new_email.strip() == "":
                return "Email cannot be empty", 400
            elif len(new_email) > 256:
                return "Email cannot be longer than 256 characters", 400
            elif not email_regex.match(new_email):
                return "Email is invalid", 400
            
            if new_email == current_user.email:
                return "Email cannot be the same as the current email", 400
            
            email = models.User.query.filter(models.User.email == new_email, models.User.deleted_at == None).first()

            if email:
                return "Email already taken", 400
            
            current_user.email = new_email
            db.session.commit()

            return jsonify({"status": "OK", "value": new_email}), 200
        elif "edit-password" in response:
            new_password = response["edit-password"]

            if not "edit-password-confirm" in response:
                return "Password confirmation required", 400
            
            new_confirm = response["edit-password-confirm"]

            if new_password.strip() == "":
                return "Password cannot be empty", 400
            
            if len(new_password) < 8 or len(new_password) > 24:
                return "Password must be between 8 and 24 characters", 400
            
            if not password_regex.match(new_password):
                return "Password is invalid", 400
            
            if new_password != new_confirm:
                return "Passwords do not match", 400
            
            current_user.set_password(new_password)
            db.session.commit()

            return jsonify({"status": "OK"}), 200
        elif "edit-colour" in response:
            new_colour = response["edit-colour"]

            if new_colour not in models.PROFILE_COLOURS:
                return "Invalid colour", 400
            
            current_user.profile_colour = new_colour
            db.session.commit()

            return jsonify({"status": "OK", "value": new_colour}), 200
        elif "delete-profile" in response:
            current_user.deleted_at = datetime.now(timezone.utc)
            db.session.commit()
            logout_user()
            flash("Your account has been deleted", "success")
            return jsonify({"status": "OK"}), 200
        else:
            return "Invalid request", 400

    user = models.User.query.filter(models.User.id == current_user.id).first()

    username=current_user.username
    colour=current_user.profile_colour

    search_form = SearchForm()
    form = WatchPartyForm()

    return render_template("profile.html", title="Profile", user=user, colours=models.PROFILE_COLOURS, username=username, colour=colour, search_form=search_form, form=form)

@app.route("/query", methods=["POST"])
@login_required
def query():
    """Queries the TMDB API and returns the results."""
    search = request.get_json()["search"].strip()

    url = f"https://api.themoviedb.org/3/search/movie?query={search}&include_adult=false&language=en-US&page=1"

    response = requests.get(url, headers=headers)
    return response.text

@app.errorhandler(404)
def page_not_found(e):
    """Render the 404 page."""
    return render_template("404.html"), 404