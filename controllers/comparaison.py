from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for

from models.db import Session
from models.dimensions import Departement, ProfessionSante, Region
from services.ameli_api import AmeliAPI

bp_comparaison = Blueprint("comparaison", __name__, url_prefix="/comparaison")

api = AmeliAPI()


def login_required(route):
    """Protege une route si l'utilisateur n'est pas connecte."""
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return route(*args, **kwargs)
    return wrapper


def _territoire_depuis_selection(db_session, region_id, departement_selection):
    region = db_session.get(Region, region_id) if region_id else None

    if not region:
        return None, None, None, "Veuillez choisir une region valide."

    france_selectionnee = str(region.code) == "99"
    region_entiere_selectionnee = departement_selection == "all"

    if france_selectionnee:
        return "999", region.code, "France entiere", None

    if region_entiere_selectionnee:
        return "999", region.code, region.libelle, None

    if not departement_selection:
        return None, None, None, "Veuillez choisir un departement valide."

    try:
        departement = db_session.get(Departement, int(departement_selection))
    except ValueError:
        departement = None

    if not departement:
        return None, None, None, "Veuillez choisir un departement valide."

    if departement.region_id != region.id:
        return None, None, None, "Le departement choisi ne correspond pas a la region."

    return departement.code, None, f"{departement.code} - {departement.libelle}", None


def _indexer_par_annee(resultats):
    donnees = {}

    for ligne in resultats:
        annee = str(ligne.get("annee", ""))[:4]

        if annee:
            donnees[annee] = ligne

    return donnees


def _dernier_point(resultats):
    valeurs = [
        ligne for ligne in resultats
        if ligne.get("effectif") not in (None, "")
    ]

    if not valeurs:
        return None

    return sorted(valeurs, key=lambda ligne: str(ligne.get("annee", "")))[-1]


def _pourcentage_ecart(valeur_a, valeur_b):
    if (
        not isinstance(valeur_a, (int, float))
        or not isinstance(valeur_b, (int, float))
        or valeur_b == 0
    ):
        return None

    return round(((valeur_a - valeur_b) / valeur_b) * 100, 1)


@bp_comparaison.route("/")
@login_required
def index():
    """Page de comparaison de deux territoires."""
    profession_id = request.args.get("profession_id", type=int)
    region_a_id = request.args.get("region_a_id", type=int)
    region_b_id = request.args.get("region_b_id", type=int)
    departement_a = request.args.get("departement_a_id")
    departement_b = request.args.get("departement_b_id")
    first_year = request.args.get("first_year", default=2010, type=int)
    last_year = request.args.get("last_year", default=2024, type=int)

    db_session = Session()

    try:
        professions = db_session.query(ProfessionSante).order_by(ProfessionSante.libelle).all()
        regions = db_session.query(Region).order_by(Region.libelle).all()
        profession = db_session.get(ProfessionSante, profession_id) if profession_id else None

        comparaison_lancee = bool(request.args)
        message_erreur = None
        resultats_a = []
        resultats_b = []
        lignes_tableau = []
        has_donnees = False
        label_a = None
        label_b = None
        dernier_a = None
        dernier_b = None
        ecart_effectif = None
        ecart_effectif_pourcentage = None
        ecart_densite = None
        ecart_densite_pourcentage = None

        if comparaison_lancee:
            if not profession:
                message_erreur = "Veuillez choisir une profession de sante valide."
            elif not first_year or not last_year:
                message_erreur = "Veuillez choisir une periode valide."
            else:
                annee_debut = min(first_year, last_year)
                annee_fin = max(first_year, last_year)

                code_a, region_code_a, label_a, erreur_a = _territoire_depuis_selection(
                    db_session,
                    region_a_id,
                    departement_a,
                )
                code_b, region_code_b, label_b, erreur_b = _territoire_depuis_selection(
                    db_session,
                    region_b_id,
                    departement_b,
                )

                message_erreur = erreur_a or erreur_b

                if not message_erreur:
                    resultats_a = api.get_effectifs(
                        profession.libelle,
                        code_a,
                        annee_debut,
                        annee_fin,
                        region_code_a,
                    )
                    erreur_api_a = api.last_error

                    resultats_b = api.get_effectifs(
                        profession.libelle,
                        code_b,
                        annee_debut,
                        annee_fin,
                        region_code_b,
                    )
                    erreur_api_b = api.last_error

                    if erreur_api_a or erreur_api_b:
                        message_erreur = erreur_api_a or erreur_api_b

                    has_donnees = bool(resultats_a or resultats_b)

                    donnees_a = _indexer_par_annee(resultats_a)
                    donnees_b = _indexer_par_annee(resultats_b)

                    for annee in range(annee_debut, annee_fin + 1):
                        cle = str(annee)
                        ligne_a = donnees_a.get(cle, {})
                        ligne_b = donnees_b.get(cle, {})
                        effectif_a = ligne_a.get("effectif")
                        effectif_b = ligne_b.get("effectif")
                        densite_a = ligne_a.get("densite")
                        densite_b = ligne_b.get("densite")

                        lignes_tableau.append({
                            "annee": annee,
                            "effectif_a": effectif_a,
                            "densite_a": densite_a,
                            "effectif_b": effectif_b,
                            "densite_b": densite_b,
                            "ecart_effectif": (
                                effectif_a - effectif_b
                                if isinstance(effectif_a, (int, float))
                                and isinstance(effectif_b, (int, float))
                                else None
                            ),
                            "ecart_effectif_pourcentage": _pourcentage_ecart(
                                effectif_a,
                                effectif_b,
                            ),
                            "ecart_densite": (
                                round(densite_a - densite_b, 2)
                                if isinstance(densite_a, (int, float))
                                and isinstance(densite_b, (int, float))
                                else None
                            ),
                            "ecart_densite_pourcentage": _pourcentage_ecart(
                                densite_a,
                                densite_b,
                            ),
                        })

                    dernier_a = _dernier_point(resultats_a)
                    dernier_b = _dernier_point(resultats_b)

                    if dernier_a and dernier_b:
                        if isinstance(dernier_a.get("effectif"), (int, float)) and isinstance(dernier_b.get("effectif"), (int, float)):
                            ecart_effectif = dernier_a["effectif"] - dernier_b["effectif"]
                            ecart_effectif_pourcentage = _pourcentage_ecart(
                                dernier_a["effectif"],
                                dernier_b["effectif"],
                            )

                        if isinstance(dernier_a.get("densite"), (int, float)) and isinstance(dernier_b.get("densite"), (int, float)):
                            ecart_densite = round(dernier_a["densite"] - dernier_b["densite"], 2)
                            ecart_densite_pourcentage = _pourcentage_ecart(
                                dernier_a["densite"],
                                dernier_b["densite"],
                            )

        return render_template(
            "comparaison.html",
            professions=professions,
            regions=regions,
            profession=profession,
            comparaison_lancee=comparaison_lancee,
            message_erreur=message_erreur,
            selected_profession_id=profession_id,
            selected_region_a_id=region_a_id,
            selected_region_b_id=region_b_id,
            selected_departement_a_id=departement_a,
            selected_departement_b_id=departement_b,
            first_year=first_year,
            last_year=last_year,
            label_a=label_a,
            label_b=label_b,
            resultats_a=resultats_a,
            resultats_b=resultats_b,
            lignes_tableau=lignes_tableau,
            has_donnees=has_donnees,
            dernier_a=dernier_a,
            dernier_b=dernier_b,
            ecart_effectif=ecart_effectif,
            ecart_effectif_pourcentage=ecart_effectif_pourcentage,
            ecart_densite=ecart_densite,
            ecart_densite_pourcentage=ecart_densite_pourcentage,
        )

    finally:
        db_session.close()
