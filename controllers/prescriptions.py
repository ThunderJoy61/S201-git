from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for
from models.db import Session
from models.dimensions import (
    Region,
    Departement,
    ProfessionSante,
    TypeHonoraire,
    TypePrescription,
    TypeSecteur,
)

bp_prescriptions = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")


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
        nb_regions = db_session.query(Region).count()
        nb_departements = db_session.query(Departement).count()
        nb_professions = db_session.query(ProfessionSante).count()
        nb_honoraires = db_session.query(TypeHonoraire).count()
        nb_prescriptions = db_session.query(TypePrescription).count()
        nb_secteurs = db_session.query(TypeSecteur).count()

        regions = (
            db_session.query(Region)
            .order_by(Region.libelle)
            .all()
        )

        # Nombre de départements par région pour le graphique
        repartition_regions = []
        for region in regions:
            nb_depts = (
                db_session.query(Departement)
                .filter_by(region_id=region.id)
                .count()
            )

            repartition_regions.append({
                "region": region.libelle,
                "departements": nb_depts
            })

        return render_template(
            "prescriptions.html",
            nb_regions=nb_regions,
            nb_departements=nb_departements,
            nb_professions=nb_professions,
            nb_honoraires=nb_honoraires,
            nb_prescriptions=nb_prescriptions,
            nb_secteurs=nb_secteurs,
            repartition_regions=repartition_regions
        )

    finally:
        db_session.close()