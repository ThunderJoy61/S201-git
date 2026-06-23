import json
import time
from copy import deepcopy

import requests


class AmeliAPI:
    """Service d'acces a l'API Data Ameli."""

    BASE_URL = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets"

    def __init__(self, timeout=10, cache_duration=300):
        self._timeout = timeout
        self._session = requests.Session()
        self.last_error = None

        # Durée du cache en secondes.
        # 300 secondes = 5 minutes.
        self._cache_duration = cache_duration

        # Cache conservé en mémoire tant que Flask reste lancé.
        self._cache = {}

    def get_effectifs(
        self,
        profession,
        departement_code,
        first_year,
        last_year,
        region_code=None
    ):
        """Effectifs pour une profession, un departement et une annee."""
        y1 = int(first_year)
        y2 = int(last_year)
        f_year = min(y1, y2)
        l_year = max(y1, y2)

        where = (
            f'profession_sante="{self._escape_value(profession)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'year(annee) >= {f_year} AND '
            f'year(annee) <= {l_year} AND '
            f'libelle_classe_age="Tout âge" AND '
            f'libelle_sexe="tout sexe"'
        )

        return self._requete(
            "demographie-effectifs-et-les-densites",
            {
                "select": "annee,effectif,densite",
                "where": where,
                "limit": 100,
                "order_by": "annee",
            },
            normalisateur=self._normaliser_resultat
        )

    def get_evolution_effectifs(
        self,
        profession,
        departement_code,
        region_code=None
    ):
        """Effectifs sur toutes les annees disponibles."""

        where = (
            f'profession_sante="{self._escape_value(profession)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'libelle_classe_age="Tout âge" AND '
            f'libelle_sexe="tout sexe"'
        )

        return self._requete(
            "demographie-effectifs-et-les-densites",
            {
                "select": "annee,effectif,densite",
                "where": where,
                "order_by": "annee",
                "limit": 100,
            },
        )

    def get_honoraires(
        self,
        type_honoraire,
        departement_code,
        first_year,
        last_year,
        region_code=None
    ):
        """Honoraires pour un type d'honoraire, un territoire et une periode."""
        y1 = int(first_year)
        y2 = int(last_year)
        f_year = min(y1, y2)
        l_year = max(y1, y2)

        france_entiere = (
            str(departement_code) == "999"
            or str(region_code) == "99"
        )

        select = (
            "annee,"
            "profession_sante,"
            "type_honoraires_niveau_1,"
            "type_honoraires_niveau_2,"
            "type_honoraires_niveau_3,"
            "montant_honoraires,"
            "montant_honoraires_moyens"
        )

        def lancer_requete(filtre_honoraire, filtre_territoire=None):
            conditions = [
                filtre_honoraire,
                f'year(annee) >= {f_year}',
                f'year(annee) <= {l_year}'
            ]

            if filtre_territoire:
                conditions.append(filtre_territoire)

            where = " AND ".join(conditions)

            return self._requete(
                "honoraires-detailles",
                {
                    "select": select,
                    "where": where,
                    "limit": 100,
                    "order_by": "montant_honoraires DESC",
                },
                normalisateur=self._normaliser_honoraires
            )

        filtre_precis = self._filtre_honoraires(
            type_honoraire,
            mode="precis"
        )

        filtre_large = self._filtre_honoraires(
            type_honoraire,
            mode="large"
        )

        if france_entiere:
            filtres_territoire_france = [
                'departement="999"',
                'region="99" AND departement="999"',
                None
            ]

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requete(
                    filtre_precis,
                    filtre_territoire
                )

                if resultats:
                    return resultats

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requete(
                    filtre_large,
                    filtre_territoire
                )

                if resultats:
                    return resultats

            return []

        filtre_territoire = self._filtre_territoire(
            departement_code,
            region_code
        )

        resultats = lancer_requete(
            filtre_precis,
            filtre_territoire
        )

        if resultats:
            return resultats

        return lancer_requete(
            filtre_large,
            filtre_territoire
        )

    def get_evolution_honoraires(
        self,
        type_honoraire,
        departement_code,
        first_year,
        last_year,
        region_code=None
    ):
        """Montants d'honoraires agreges par annee pour le graphique."""
        y1 = int(first_year)
        y2 = int(last_year)
        f_year = min(y1, y2)
        l_year = max(y1, y2)

        france_entiere = (
            str(departement_code) == "999"
            or str(region_code) == "99"
        )

        filtre_precis = self._filtre_honoraires(
            type_honoraire,
            mode="precis"
        )

        filtre_large = self._filtre_honoraires(
            type_honoraire,
            mode="large"
        )

        def total_annuel(
            annee,
            filtre_honoraire,
            filtre_territoire=None
        ):
            conditions = [
                filtre_honoraire,
                f'year(annee) = {annee}'
            ]

            if filtre_territoire:
                conditions.append(filtre_territoire)

            resultats = self._requete(
                "honoraires-detailles",
                {
                    "select": (
                        "sum(montant_honoraires) "
                        "as montant_honoraires"
                    ),
                    "where": " AND ".join(conditions),
                    "limit": 1,
                }
            )

            if not resultats:
                return None

            montant = self._to_number(
                resultats[0].get("montant_honoraires")
            )

            return {
                "annee": annee,
                "montant_honoraires": montant,
            }

        def lancer_requetes_annuelles(
            filtre_honoraire,
            filtre_territoire=None
        ):
            resultats = []

            for annee in range(f_year, l_year + 1):
                total = total_annuel(
                    annee,
                    filtre_honoraire,
                    filtre_territoire
                )

                if (
                    total
                    and total["montant_honoraires"] is not None
                ):
                    resultats.append(total)

            return resultats

        if france_entiere:
            filtres_territoire_france = [
                'departement="999"',
                'region="99" AND departement="999"',
                None
            ]

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requetes_annuelles(
                    filtre_precis,
                    filtre_territoire
                )

                if resultats:
                    return resultats

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requetes_annuelles(
                    filtre_large,
                    filtre_territoire
                )

                if resultats:
                    return resultats

            return []

        filtre_territoire = self._filtre_territoire(
            departement_code,
            region_code
        )

        resultats = lancer_requetes_annuelles(
            filtre_precis,
            filtre_territoire
        )

        if resultats:
            return resultats

        return lancer_requetes_annuelles(
            filtre_large,
            filtre_territoire
        )

    def get_prescriptions(
        self,
        type_prescription,
        departement_code,
        year,
        region_code=None
    ):
        """Prescriptions pour un type, un departement et une annee."""

        where = (
            f'libelle_poste_prescription="'
            f'{self._escape_value(type_prescription)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'year(annee) >= {year} AND '
            f'year(annee) <= {year}'
        )

        return self._requete(
            "prescriptions",
            {
                "select": (
                    "annee,"
                    "profession_sante,"
                    "libelle_poste_prescription,"
                    "montant_total_prescription_integer,"
                    "montant_moyen_prescription_integer"
                ),
                "where": where,
                "limit": 100,
                "order_by": (
                    "montant_total_prescription_integer DESC"
                ),
            },
        )

    def get_repartition_sexe(
        self,
        profession,
        departement_code,
        year,
        region_code=None
    ):
        """
        Récupère la répartition par sexe pour une profession,
        un territoire et une année.
        """
        where = (
            f'profession_sante="{self._escape_value(profession)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'year(annee) = {int(year)} AND '
            f'libelle_classe_age="Tout âge" AND '
            f'libelle_sexe!="tout sexe"'
        )

        return self._requete(
            "demographie-effectifs-et-les-densites",
            {
                "select": "libelle_sexe,effectif",
                "where": where,
                "limit": 100,
            }
        )

    def get_repartition_age(
        self,
        profession,
        departement_code,
        year,
        region_code=None
    ):
        """
        Récupère la répartition par tranche d'âge pour une profession,
        un territoire et une année.
        """
        where = (
            f'profession_sante="{self._escape_value(profession)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'year(annee) = {int(year)} AND '
            f'libelle_classe_age!="Tout âge" AND '
            f'libelle_sexe="tout sexe"'
        )

        return self._requete(
            "demographie-effectifs-et-les-densites",
            {
                "select": "libelle_classe_age,effectif",
                "where": where,
                "limit": 100,
            }
        )

    def _creer_cle_cache(
        self,
        dataset,
        params,
        normalisateur=None
    ):
        """
        Crée une clé unique selon le dataset,
        les paramètres et le normalisateur.
        """
        nom_normalisateur = (
            normalisateur.__name__
            if normalisateur is not None
            else "sans_normalisateur"
        )

        contenu = {
            "dataset": dataset,
            "params": params,
            "normalisateur": nom_normalisateur,
        }

        return json.dumps(
            contenu,
            sort_keys=True,
            ensure_ascii=False,
            default=str
        )

    def _lire_cache(self, cle_cache):
        """
        Retourne les résultats du cache
        s'ils existent encore et ne sont pas expirés.
        """
        entree = self._cache.get(cle_cache)

        if entree is None:
            return None

        age = time.time() - entree["date"]

        if age >= self._cache_duration:
            del self._cache[cle_cache]

            print(
                "[AmeliAPI] Cache expiré, "
                "nouvel appel de l'API."
            )

            return None

        print(
            "[AmeliAPI] Cache utilisé, "
            f"âge : {age:.1f} seconde(s)."
        )

        return deepcopy(entree["resultats"])

    def _enregistrer_cache(self, cle_cache, resultats):
        """Enregistre les résultats d'une requête dans le cache."""
        self._cache[cle_cache] = {
            "date": time.time(),
            "resultats": deepcopy(resultats),
        }

        print(
            "[AmeliAPI] Résultats enregistrés "
            f"dans le cache pour {self._cache_duration} seconde(s)."
        )

    def vider_cache(self):
        """Vide manuellement toutes les réponses enregistrées."""
        self._cache.clear()
        print("[AmeliAPI] Cache vidé.")

    def nettoyer_cache(self):
        """Supprime les entrées du cache qui ont expiré."""
        maintenant = time.time()

        cles_expirees = [
            cle_cache
            for cle_cache, entree in self._cache.items()
            if maintenant - entree["date"] >= self._cache_duration
        ]

        for cle_cache in cles_expirees:
            del self._cache[cle_cache]

        if cles_expirees:
            print(
                f"[AmeliAPI] {len(cles_expirees)} "
                "entrée(s) expirée(s) supprimée(s)."
            )

    def _requete(self, dataset, params, normalisateur=None):
        url = f"{self.BASE_URL}/{dataset}/records"
        self.last_error = None

        # Nettoyage des anciennes entrées avant chaque requête.
        self.nettoyer_cache()

        cle_cache = self._creer_cle_cache(
            dataset,
            params,
            normalisateur
        )

        resultats_cache = self._lire_cache(cle_cache)

        if resultats_cache is not None:
            return resultats_cache

        print("\n--- URL API ---")
        print(url)
        print("--- PARAMS ---")
        print(params)
        print("[AmeliAPI] Aucun cache disponible, appel de l'API.")

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._timeout
            )

            print("--- STATUS ---")
            print(response.status_code)
            print("--- REPONSE API ---")
            print(response.text[:1000])

            response.raise_for_status()

            resultats_bruts = response.json().get("results", [])

            if normalisateur:
                resultats = [
                    normalisateur(resultat)
                    for resultat in resultats_bruts
                ]
            else:
                resultats = resultats_bruts

            # Seules les requêtes réussies sont mises en cache.
            self._enregistrer_cache(
                cle_cache,
                resultats
            )

            return deepcopy(resultats)

        except requests.RequestException as e:
            self.last_error = (
                "Erreur lors de l'appel Data Ameli : "
                f"{e}"
            )

            print(f"[AmeliAPI] {self.last_error}")

            # Une erreur API n'est jamais enregistrée dans le cache.
            return []

        except ValueError as e:
            self.last_error = (
                "La réponse de Data Ameli n'est pas "
                f"un JSON valide : {e}"
            )

            print(f"[AmeliAPI] {self.last_error}")

            return []

    @staticmethod
    def _valeur_honoraire_valide(value):
        if value is None:
            return False

        texte = str(value).strip()

        return texte not in (
            "",
            "None",
            "NULL",
            "null",
            "nan",
            "NaN",
            "—",
            "-"
        )

    @staticmethod
    def _escape_value(value):
        if value is None:
            return ""

        return str(value).replace('"', '\\"')

    def _filtre_territoire(
        self,
        departement_code,
        region_code=None
    ):
        if region_code is None:
            return (
                f'departement="'
                f'{self._escape_value(str(departement_code))}"'
            )

        return (
            f'region="{self._escape_value(str(region_code))}" AND '
            f'departement="'
            f'{self._escape_value(str(departement_code))}"'
        )

    def _filtre_honoraires(
        self,
        type_honoraire,
        mode="precis"
    ):
        niveau_1 = getattr(
            type_honoraire,
            "niveau_1",
            None
        )

        niveau_2 = getattr(
            type_honoraire,
            "niveau_2",
            None
        )

        niveau_3 = getattr(
            type_honoraire,
            "niveau_3",
            None
        )

        conditions = []

        if self._valeur_honoraire_valide(niveau_1):
            conditions.append(
                f'type_honoraires_niveau_1="'
                f'{self._escape_value(niveau_1)}"'
            )

        # Mode large : filtre uniquement sur niveau_1.
        if mode == "large":
            if conditions:
                return " AND ".join(conditions)

            return 'type_honoraires_niveau_1="Actes"'

        if self._valeur_honoraire_valide(niveau_2):
            conditions.append(
                f'type_honoraires_niveau_2="'
                f'{self._escape_value(niveau_2)}"'
            )

        if self._valeur_honoraire_valide(niveau_3):
            conditions.append(
                f'type_honoraires_niveau_3="'
                f'{self._escape_value(niveau_3)}"'
            )

        if not conditions:
            return 'type_honoraires_niveau_1="Actes"'

        return " AND ".join(conditions)

    @staticmethod
    def _normaliser_resultat(resultat):
        """Convertit les valeurs API en champs simples pour les templates."""
        return {
            "annee": resultat.get("annee"),
            "effectif": AmeliAPI._to_number(
                resultat.get("effectif")
            ),
            "densite": AmeliAPI._to_number(
                resultat.get("densite")
            ),
        }

    @staticmethod
    def _normaliser_honoraires(resultat):
        """
        Convertit les valeurs API honoraires
        en champs simples pour les templates.
        """
        return {
            "annee": resultat.get("annee"),
            "profession_sante": resultat.get(
                "profession_sante"
            ),
            "niveau_1": resultat.get(
                "type_honoraires_niveau_1"
            ),
            "niveau_2": resultat.get(
                "type_honoraires_niveau_2"
            ),
            "niveau_3": resultat.get(
                "type_honoraires_niveau_3"
            ),
            "montant_honoraires": AmeliAPI._to_number(
                resultat.get("montant_honoraires")
            ),
            "montant_honoraires_moyens": AmeliAPI._to_number(
                resultat.get("montant_honoraires_moyens")
            ),
        }

    @staticmethod
    def _normaliser_evolution_honoraires(resultat):
        """
        Convertit les totaux d'honoraires
        par annee pour le graphique.
        """
        return {
            "annee": resultat.get("annee"),
            "montant_honoraires": AmeliAPI._to_number(
                resultat.get("montant_honoraires")
            ),
        }

    @staticmethod
    def _to_number(value):
        if value is None or value == "":
            return None

        if isinstance(value, (int, float)):
            return value

        texte = str(value).replace(",", ".")

        try:
            nombre = float(texte)
        except ValueError:
            return value

        return (
            int(nombre)
            if nombre.is_integer()
            else nombre
        )