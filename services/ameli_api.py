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
        return value.replace('"', '\\"')

    def _filtre_territoire(self, departement_code, region_code=None):
        if region_code is None:
            return f'departement="{self._escape_value(str(departement_code))}"'

        return (
            f'region="{self._escape_value(str(region_code))}" AND '
            f'departement="{self._escape_value(str(departement_code))}"'
        )

    @staticmethod
    def _normaliser_resultat(resultat):
        """Convertit les valeurs API en champs simples pour les templates."""
        return {
            "annee": resultat.get("annee"),
            "effectif": AmeliAPI._to_number(resultat.get("effectif")),
            "densite": AmeliAPI._to_number(resultat.get("densite")),
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