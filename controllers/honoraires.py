from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, request
from services.ameli_api import AmeliAPI
from models.db import Session
from models.dimensions import (
    Region,
    Departement,
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
    """Page d'analyse des honoraires."""
    db_session = Session()

    resultats = []
    evolution_honoraires = []
    recherche_lancee = False
    honoraire_selectionne = None
    departement_selectionne = None
    territoire_label = None
    message_erreur = None

    selected_honoraires_id = request.args.get("honoraires_id", type=int)
    selected_region_id = request.args.get("region_id", type=int)
    departement_selection = request.args.get("departement_id")
    first_year = request.args.get("first_year", default=2010, type=int)
    last_year = request.args.get("last_year", default=2024, type=int)

    try:
        regions = db_session.query(Region).order_by(Region.libelle).all()

        honoraires = db_session.query(TypeHonoraire).order_by(
            TypeHonoraire.niveau_1,
            TypeHonoraire.niveau_2,
            TypeHonoraire.niveau_3
        ).all()

        # Dès qu'il y a des paramètres dans l'URL, on considère que l'utilisateur a lancé une recherche
        if request.args:
            recherche_lancee = True

        region_selectionnee = None

        if selected_region_id:
            region_selectionnee = db_session.get(Region, selected_region_id)

        if selected_honoraires_id:
            honoraire_selectionne = db_session.get(TypeHonoraire, selected_honoraires_id)

        # Cas normal : département existant dans la BDD
        france_selectionnee = region_selectionnee and region_selectionnee.code == "99"
        region_entiere_selectionnee = departement_selection == "all"

        if (
            not france_selectionnee
            and not region_entiere_selectionnee
            and departement_selection
        ):
            try:
                departement_selectionne = db_session.get(
                    Departement,
                    int(departement_selection)
                )
            except ValueError:
                departement_selectionne = None

        # Cas spécial : France entière
        if france_selectionnee:
            departement_code = "999"
            territoire_label = "France entière"
        elif region_entiere_selectionnee:
            departement_code = "999"
            territoire_label = region_selectionnee.libelle if region_selectionnee else None
        elif departement_selectionne:
            departement_code = departement_selectionne.code
            territoire_label = f"{departement_selectionne.code} — {departement_selectionne.libelle}"
        else:
            departement_code = None

        if recherche_lancee:
            if not honoraire_selectionne:
                message_erreur = "Veuillez choisir un type d’honoraire valide."

            elif not region_selectionnee:
                message_erreur = "Veuillez choisir une région valide."

            elif not departement_code:
                message_erreur = "Veuillez choisir un département valide."

            elif (
                departement_selectionne
                and departement_selectionne.region_id != region_selectionnee.id
            ):
                message_erreur = "Le departement choisi ne correspond pas a la region."

            else:
                resultats = api.get_honoraires(
                    honoraire_selectionne,
                    departement_code,
                    first_year,
                    last_year,
                    region_selectionnee.code
                )
                evolution_honoraires = api.get_evolution_honoraires(
                    honoraire_selectionne,
                    departement_code,
                    first_year,
                    last_year,
                    region_selectionnee.code
                )

        return render_template(
            "honoraires.html",
            regions=regions,
            honoraires=honoraires,
            resultats=resultats,
            evolution_honoraires=evolution_honoraires,
            recherche_lancee=recherche_lancee,
            honoraire_selectionne=honoraire_selectionne,
            departement_selectionne=departement_selectionne,
            territoire_label=territoire_label,
            selected_honoraires_id=selected_honoraires_id,
            selected_region_id=selected_region_id,
            selected_departement_id=departement_selection,
            first_year=first_year,
            last_year=last_year,
            api_error=api.last_error,
            message_erreur=message_erreur,
        )

    finally:
        db_session.close()
