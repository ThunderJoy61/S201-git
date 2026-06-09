import os
from flask import Blueprint, render_template, request, redirect, url_for, session

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    """Page de connexion."""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        if username == admin_username and password == admin_password:
            session["user"] = username
            return redirect(url_for("dashboard.index"))

        return render_template(
            "login.html",
            erreur="Identifiant ou mot de passe incorrect."
        )

    return render_template("login.html")


@bp_auth.route("/logout")
def logout():
    """Déconnexion."""
    session.clear()
    return redirect(url_for("accueil.index"))