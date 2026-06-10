from flask import Blueprint, render_template
from services.ameli_api import AmeliAPI
from models.db import Session
from models.dimensions import Region, ProfessionSante

bp_accueil = Blueprint("accueil", __name__)

api = AmeliAPI()

@bp_accueil.route("/")
def index():
    """Page d'accueil."""
    session = Session()

    try:
        regions = session.query(Region).order_by(Region.libelle).all()
        professions = session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        preview = api.get_effectifs("Infirmiers", "999", 2024, 2024, "99")
        evolution = api.get_evolution_effectifs("Infirmiers", "999", "99")

        return render_template(
            "accueil.html",
            regions=regions,
            professions=professions,
            preview=preview,
            evolution=evolution
        )

    finally:
        session.close()