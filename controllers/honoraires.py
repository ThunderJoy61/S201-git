from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for
from services.ameli_api import AmeliAPI
from models.db import Session
from models.dimensions import (
    Region,
    TypeHonoraire,
)

bp_honoraires = Blueprint("honoraires", __name__, url_prefix="/honoraires")

api = AmeliAPI()

def login_required(route):
    """Protège une route si l'utilisateur n'est pas connecté."""
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return route(*args, **kwargs)
    return wrapper

@bp_honoraires.route("/")
@login_required
def index():
    """Tableau de bord principal."""
    db_session = Session()

    try:
        regions = db_session.query(Region).order_by(Region.libelle).all()
        honoraires = db_session.query(TypeHonoraire).order_by(TypeHonoraire.niveau_1).all()

        return render_template(
            "honoraires.html",
            regions=regions,
            honoraires=honoraires,
            api_error=api.last_error,
        )

    finally:
        db_session.close()