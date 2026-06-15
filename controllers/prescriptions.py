from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, request
from services.ameli_api import AmeliAPI
from models.db import Session
from models.dimensions import (
    Departement,
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

@bp_prescriptions.route("/resultats")
@login_required
def resultats():
    prescription_id = request.args.get("prescription_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_selection = request.args.get("departement_id")
    year = request.args.get("year", type=int)

    db_session = Session()

    try:
        prescriptions = db_session.get(TypePrescription, prescription_id)
        region = db_session.get(Region, region_id)
        france_selectionnee = region and region.code == "99"
        region_entiere_selectionnee = departement_selection == "all"
        dept = None

        if not france_selectionnee and not region_entiere_selectionnee and departement_selection:
            try:
                dept = db_session.get(Departement, int(departement_selection))
            except ValueError:
                dept = None

        if (
            not prescriptions
            or not region
            or not year
            or (not france_selectionnee and not region_entiere_selectionnee and not dept)
            or (dept and dept.region_id != region.id)
        ):
            return render_template(
                "erreur.html",
                message="Parametres manquants ou invalides.",
            ), 400

        if france_selectionnee:
            territoire_label = "FRANCE"
            resultats = api.get_prescriptions(type_prescription=prescriptions.libelle, departement_code="999", year=year, region_code=region.code)
        elif region_entiere_selectionnee:
            territoire_label = region.libelle
            resultats = api.get_prescriptions(type_prescription=prescriptions.libelle, departement_code="999", year=year, region_code=region.code)
        else:
            territoire_label = f"{dept.code} - {dept.libelle}"
            resultats = api.get_prescriptions(type_prescription=prescriptions.libelle, departement_code=dept.code, year=year, region_code=region.code)

        return render_template(
            "prescriptionsr.html",
            prescriptions=prescriptions,
            dept=dept,
            region=region,
            territoire_label=territoire_label,
            year=year,
            resultats=resultats,
            api_error=api.last_error,
        )
    finally:
        db_session.close()