import requests


class AmeliAPI:
    """Service d'acces a l'API Data Ameli."""

    BASE_URL = "https://data.ameli.fr/api/explore/v2.1/catalog/datasets"

    def __init__(self, timeout=10):
        self._timeout = timeout
        self._session = requests.Session()
        self.last_error = None

    def get_effectifs(self, profession, departement_code, first_year, last_year, region_code=None):
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

    def get_evolution_effectifs(self, profession, departement_code, region_code=None):
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

    def get_honoraires(self, type_honoraire, departement_code, first_year, last_year, region_code=None):
        """Honoraires pour un type d'honoraire, un territoire et une periode."""
        y1 = int(first_year)
        y2 = int(last_year)
        f_year = min(y1, y2)
        l_year = max(y1, y2)

        france_entiere = str(departement_code) == "999" or str(region_code) == "99"

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
                    "order_by": "annee,profession_sante",
                },
                normalisateur=self._normaliser_honoraires
            )

        filtre_precis = self._filtre_honoraires(type_honoraire, mode="precis")
        filtre_large = self._filtre_honoraires(type_honoraire, mode="large")

        if france_entiere:
            filtres_territoire_france = [
                'departement="999"',
                'region="99" AND departement="999"',
                None
            ]

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requete(filtre_precis, filtre_territoire)
                if resultats:
                    return resultats

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requete(filtre_large, filtre_territoire)
                if resultats:
                    return resultats

            return []

        filtre_territoire = self._filtre_territoire(departement_code, region_code)

        resultats = lancer_requete(filtre_precis, filtre_territoire)
        if resultats:
            return resultats

        return lancer_requete(filtre_large, filtre_territoire)

    def get_evolution_honoraires(self, type_honoraire, departement_code, first_year, last_year, region_code=None):
        """Montants d'honoraires agreges par annee pour le graphique."""
        y1 = int(first_year)
        y2 = int(last_year)
        f_year = min(y1, y2)
        l_year = max(y1, y2)

        france_entiere = str(departement_code) == "999" or str(region_code) == "99"
        filtre_precis = self._filtre_honoraires(type_honoraire, mode="precis")
        filtre_large = self._filtre_honoraires(type_honoraire, mode="large")

        def total_annuel(annee, filtre_honoraire, filtre_territoire=None):
            conditions = [
                filtre_honoraire,
                f'year(annee) = {annee}'
            ]

            if filtre_territoire:
                conditions.append(filtre_territoire)

            resultats = self._requete(
                "honoraires-detailles",
                {
                    "select": "sum(montant_honoraires) as montant_honoraires",
                    "where": " AND ".join(conditions),
                    "limit": 1,
                }
            )

            if not resultats:
                return None

            montant = self._to_number(resultats[0].get("montant_honoraires"))
            return {
                "annee": annee,
                "montant_honoraires": montant,
            }

        def lancer_requetes_annuelles(filtre_honoraire, filtre_territoire=None):
            resultats = []

            for annee in range(f_year, l_year + 1):
                total = total_annuel(annee, filtre_honoraire, filtre_territoire)

                if total and total["montant_honoraires"] is not None:
                    resultats.append(total)

            return resultats

        if france_entiere:
            filtres_territoire_france = [
                'departement="999"',
                'region="99" AND departement="999"',
                None
            ]

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requetes_annuelles(filtre_precis, filtre_territoire)
                if resultats:
                    return resultats

            for filtre_territoire in filtres_territoire_france:
                resultats = lancer_requetes_annuelles(filtre_large, filtre_territoire)
                if resultats:
                    return resultats

            return []

        filtre_territoire = self._filtre_territoire(departement_code, region_code)

        resultats = lancer_requetes_annuelles(filtre_precis, filtre_territoire)
        if resultats:
            return resultats

        return lancer_requetes_annuelles(filtre_large, filtre_territoire)

    @staticmethod
    def _valeur_honoraire_valide(value):
        if value is None:
            return False

        texte = str(value).strip()

        return texte not in ("", "None", "NULL", "null", "nan", "NaN", "—", "-")

    def _requete(self, dataset, params, normalisateur=None):
        url = f"{self.BASE_URL}/{dataset}/records"
        self.last_error = None

        print("\n--- URL API ---")
        print(url)
        print("--- PARAMS ---")
        print(params)

        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            print("--- STATUS ---")
            print(response.status_code)
            print("--- REPONSE API ---")
            print(response.text[:1000])

            response.raise_for_status()

            if normalisateur:
                return [normalisateur(r) for r in response.json().get("results", [])]

            return response.json().get("results", [])

        except requests.RequestException as e:
            self.last_error = f"Erreur lors de l'appel Data Ameli : {e}"
            print(f"[AmeliAPI] {self.last_error}")
            return []

    @staticmethod
    def _escape_value(value):
        if value is None:
            return ""

        return str(value).replace('"', '\\"')

    def _filtre_territoire(self, departement_code, region_code=None):
        if region_code is None:
            return f'departement="{self._escape_value(str(departement_code))}"'

        return (
            f'region="{self._escape_value(str(region_code))}" AND '
            f'departement="{self._escape_value(str(departement_code))}"'
        )

    def _filtre_honoraires(self, type_honoraire, mode="precis"):
        niveau_1 = getattr(type_honoraire, "niveau_1", None)
        niveau_2 = getattr(type_honoraire, "niveau_2", None)
        niveau_3 = getattr(type_honoraire, "niveau_3", None)

        conditions = []

        if self._valeur_honoraire_valide(niveau_1):
            conditions.append(
                f'type_honoraires_niveau_1="{self._escape_value(niveau_1)}"'
            )

        # Mode large = on filtre seulement sur niveau_1
        if mode == "large":
            return " AND ".join(conditions)

        if self._valeur_honoraire_valide(niveau_2):
            conditions.append(
                f'type_honoraires_niveau_2="{self._escape_value(niveau_2)}"'
            )

        if self._valeur_honoraire_valide(niveau_3):
            conditions.append(
                f'type_honoraires_niveau_3="{self._escape_value(niveau_3)}"'
            )

        if not conditions:
            return 'type_honoraires_niveau_1="Actes"'

        return " AND ".join(conditions)
    @staticmethod
    def _normaliser_resultat(resultat):
        """Convertit les valeurs API en champs simples pour les templates."""
        return {
            "annee": resultat.get("annee"),
            "effectif": AmeliAPI._to_number(resultat.get("effectif")),
            "densite": AmeliAPI._to_number(resultat.get("densite")),
        }

    @staticmethod
    def _normaliser_honoraires(resultat):
        """Convertit les valeurs API honoraires en champs simples pour les templates."""
        return {
            "annee": resultat.get("annee"),
            "profession_sante": resultat.get("profession_sante"),
            "niveau_1": resultat.get("type_honoraires_niveau_1"),
            "niveau_2": resultat.get("type_honoraires_niveau_2"),
            "niveau_3": resultat.get("type_honoraires_niveau_3"),
            "montant_honoraires": AmeliAPI._to_number(resultat.get("montant_honoraires")),
            "montant_honoraires_moyens": AmeliAPI._to_number(resultat.get("montant_honoraires_moyens")),
        }

    @staticmethod
    def _normaliser_evolution_honoraires(resultat):
        """Convertit les totaux d'honoraires par annee pour le graphique."""
        return {
            "annee": resultat.get("annee"),
            "montant_honoraires": AmeliAPI._to_number(resultat.get("montant_honoraires")),
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

        return int(nombre) if nombre.is_integer() else nombre

    def get_prescriptions(self, type_prescription, departement_code, year, region_code=None):
        """Effectifs pour un type de prescriptions, un departement et une annee."""

        where = (
            f'libelle_poste_prescription="{self._escape_value(type_prescription)}" AND '
            f'{self._filtre_territoire(departement_code, region_code)} AND '
            f'year(annee) >= {year} AND '
            f'year(annee) <= {year}'
        )

        return self._requete(
            "prescriptions",
            {
                "select": "annee, profession_sante,libelle_poste_prescription,montant_total_prescription_integer,montant_moyen_prescription_integer",
                "where": where,
                "limit": 100,
                "order_by": "annee",
            },
        )
