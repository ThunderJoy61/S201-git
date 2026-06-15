from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for
from services.ameli_api import AmeliAPI
from models.db import Session
from models.dimensions import (
    Region,
    TypePrescription,
)

bp_prescriptions = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")

api = AmeliAPI()

def login_required(route):
    """Protège une route si l'utilisateur n'est pas connecté."""
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return route(*args, **kwargs)
    return wrapper

@bp_prescriptions.route("/")
@login_required
def index():
    """Tableau de bord principal."""
    db_session = Session()

    try:
        regions = db_session.query(Region).order_by(Region.libelle).all()
        prescriptions = db_session.query(TypePrescription).order_by(TypePrescription.libelle).all()

        return render_template(
            "prescriptions.html",
            regions=regions,
            prescriptions=prescriptions,
            api_error=api.last_error,
        )

    finally:
        db_session.close()