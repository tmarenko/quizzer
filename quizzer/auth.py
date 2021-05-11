import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from quizzer.db import get_db
from quizzer.localization import locale

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
        g.is_admin = False
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )
        g.is_admin = True if (g.user is not None and g.user['is_admin'] == 1) else False


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the password for security.
    """
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = locale.error_no_username
        elif not password:
            error = locale.error_no_password
        elif db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone() is not None:
            error = locale.error_username_is_taken.format(username=username)

        if error is None:
            db.execute(
                "INSERT INTO user (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = locale.error_incorrect_username
        elif not check_password_hash(user["password"], password):
            error = locale.error_incorrect_password

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
