from flask import Blueprint, render_template, request
from models.db import Session
from models.dimensions import Departement, ProfessionSante, Region, TrancheAge, Sexe
from services.ameli_api import AmeliAPI

bp_effectifs = Blueprint("effectifs", __name__)

api = AmeliAPI()


@bp_effectifs.route("/effectifs")
def afficher():
    profession_id = request.args.get("profession_id", type=int)
    region_id = request.args.get("region_id", type=int)
    departement_selection = request.args.get("departement_id")
    first_year = request.args.get("first_year", type=int)
    last_year = request.args.get("last_year", type=int)
    year = request.args.get("year", type=int) or 2024

    session = Session()

    try:
        prof = session.get(ProfessionSante, profession_id)
        region = session.get(Region, region_id)
        france_selectionnee = region and region.code == "99"
        region_entiere_selectionnee = departement_selection == "all"
        dept = None

        if not france_selectionnee and not region_entiere_selectionnee and departement_selection:
            try:
                dept = session.get(Departement, int(departement_selection))
            except ValueError:
                dept = None

        if (
            not prof
            or not region
            or not first_year
            or not last_year
            or (not france_selectionnee and not region_entiere_selectionnee and not dept)
            or (dept and dept.region_id != region.id)
        ):
            return render_template(
                "erreur.html",
                message="Parametres manquants ou invalides.",
            ), 400

        sexe = []
        age = []

        if france_selectionnee:
            territoire_label = "FRANCE"
            resultats = api.get_effectifs(prof.libelle, "999", first_year, last_year, region.code)
            evolution = api.get_evolution_effectifs(prof.libelle, "999", region.code)
            sexe = api.get_repartition_sexe(prof.libelle, "999", last_year, region.code)
            age = api.get_repartition_age(prof.libelle, "999", last_year, region.code)
        elif region_entiere_selectionnee:
            territoire_label = region.libelle
            resultats = api.get_effectifs(prof.libelle, "999", first_year, last_year, region.code)
            evolution = api.get_evolution_effectifs(prof.libelle, "999", region.code)
            sexe = api.get_repartition_sexe(prof.libelle, "999", year, region.code)
            age = api.get_repartition_age(prof.libelle, "999", year, region.code)
        else:
            territoire_label = f"{dept.code} - {dept.libelle}"
            resultats = api.get_effectifs(prof.libelle, dept.code, first_year, last_year)
            evolution = api.get_evolution_effectifs(prof.libelle, dept.code)
            sexe = api.get_repartition_sexe(prof.libelle, dept.code, year)
            age = api.get_repartition_age(prof.libelle, dept.code, year)

        # --- TRANSFORMATION ET ALIGNEMENT AVEC LES TABLES DIMENSIONS DE LA BDD ---
        api_sexe_dict = {str(item.get("libelle_sexe")).strip().lower(): AmeliAPI._to_number(item.get("effectif")) for item in sexe}
        api_age_dict = {str(item.get("libelle_classe_age")).strip().lower(): AmeliAPI._to_number(item.get("effectif")) for item in age}

        liste_sexes_bdd = session.query(Sexe).all()
        sexe_labels = []
        sexe_data = []
        for s in liste_sexes_bdd:
            sexe_labels.append(s.libelle)
            sexe_data.append(api_sexe_dict.get(s.libelle.lower(), 0))

        liste_ages_bdd = session.query(TrancheAge).all()
        age_labels = []
        age_data = []
        for a in liste_ages_bdd:
            age_labels.append(a.libelle)
            age_data.append(api_age_dict.get(a.libelle.lower(), 0))
        
        return render_template(
            "effectifs.html",
            prof=prof,
            dept=dept,
            region=region,
            territoire_label=territoire_label,
            first_year=first_year,
            last_year=last_year,
            year=year,
            sexe=sexe_data,
            sexe_data=sexe_data,
            sexe_labels=sexe_labels,
            age=age_data,
            age_data=age_data,
            age_labels=age_labels,
            resultats=resultats,
            evolution=evolution,
            api_error=api.last_error,
        )
    finally:
        session.close()
