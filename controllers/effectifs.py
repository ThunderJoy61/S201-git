from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import Departement, ProfessionSante, Region
from services.ameli_api import AmeliAPI

bp_effectifs = Blueprint("effectifs", __name__)

api = AmeliAPI()


@bp_effectifs.route("/effectifs")
def afficher():
    profession_id = request.args.get("profession_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_id = request.args.get("departement_id", type=int)
    annee = request.args.get("annee", type=int)

    session = Session()

    try:
        prof = session.get(ProfessionSante, profession_id)
        region = session.get(Region, region_id)
        france_selectionnee = region and region.code == "99"
        dept = None if france_selectionnee else session.get(Departement, departement_id)

        if not prof or not region or not annee or (not france_selectionnee and not dept):
            return render_template(
                "erreur.html",
                message="Parametres manquants ou invalides.",
            ), 400

        if france_selectionnee:
            territoire_label = "FRANCE"
            resultats = api.get_effectifs(prof.libelle, "999", annee, region.code)
            evolution = api.get_evolution_effectifs(prof.libelle, "999", region.code)
        else:
            territoire_label = f"{dept.code} - {dept.libelle}"
            resultats = api.get_effectifs(prof.libelle, dept.code, annee)
            evolution = api.get_evolution_effectifs(prof.libelle, dept.code)

        return render_template(
            "effectifs.html",
            prof=prof,
            dept=dept,
            region=region,
            territoire_label=territoire_label,
            annee=annee,
            resultats=resultats,
            evolution=evolution,
            api_error=api.last_error,
        )
    finally:
        session.close()
