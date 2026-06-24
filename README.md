<p align="center">
  <img src="static/images/DataLynx_fondblanc.png" alt="Logo DataLynx" width="220">
</p>

<h1 align="center">DataLynx</h1>

<p align="center">
  Application web Flask d'exploration et de visualisation des données publiques de santé de l'Assurance Maladie.
</p>

## Présentation

DataLynx a été réalisé dans le cadre de la SAÉ 2.01 du BUT Informatique de l'IUT de Créteil-Vitry, en continuité avec la SAÉ 2.04 consacrée à la base de données. L'application rend les données de [Data Ameli](https://data.ameli.fr/) plus accessibles au moyen de formulaires, d'indicateurs, de tableaux et de graphiques interactifs.

Elle combine deux sources :

- une base MySQL issue de la SAÉ 2.04, utilisée pour alimenter les listes de régions, départements, professions et catégories ;
- l'API publique Data Ameli, interrogée en temps réel pour récupérer les mesures de santé.

L'interface s'adresse principalement aux étudiants, enseignants et utilisateurs souhaitant explorer des données de santé françaises sans manipuler directement l'API.

## Fonctionnalités

### Accès public

- page d'accueil et présentation de la source Data Ameli ;
- sélection en cascade d'une région puis d'un département, sans rechargement de page ;
- consultation des effectifs et densités par profession, territoire et période ;
- évolution temporelle des effectifs ;
- répartitions par sexe et par tranche d'âge ;
- tableaux, indicateurs et graphiques Chart.js ;
- export CSV du tableau des effectifs ;
- pages d'erreur dédiées pour les erreurs HTTP 404 et 500.

### Accès authentifié

- tableau de bord synthétique sur les dimensions disponibles en base ;
- analyse des honoraires par catégorie, territoire et année, avec évolution de 2010 à 2024 ;
- analyse des prescriptions par poste, territoire et année ;
- comparaison de deux territoires sur une période donnée ;
- calcul des écarts absolus et relatifs d'effectif et de densité ;
- exports CSV des tableaux d'honoraires, de prescriptions et de comparaison ;
- déconnexion et protection des pages privées par session Flask.

### Comportement transversal

- prise en charge d'un département, d'une région entière ou de la France entière ;
- cache mémoire des réponses Data Ameli pendant 300 secondes afin de limiter les appels réseau ;
- normalisation des nombres renvoyés par l'API ;
- message explicite en cas d'indisponibilité ou de réponse invalide de l'API ;
- interface responsive, menu latéral mobile et écran de chargement.

## Technologies

| Domaine | Technologies |
| --- | --- |
| Back-end | Python 3.10+, Flask, Jinja2 |
| Accès aux données | SQLAlchemy, PyMySQL, MySQL |
| API HTTP | Requests, API Explore v2.1 de Data Ameli |
| Front-end | HTML, CSS, JavaScript natif, Fetch API |
| Visualisation | Chart.js chargé depuis jsDelivr |
| Configuration | python-dotenv et variables d'environnement |

## Architecture

Le projet suit une organisation MVC adaptée à Flask :

```text
.
├── app.py                         # Création de l'application et enregistrement des Blueprints
├── config.py                      # Variables d'environnement et URL MySQL
├── requirements.txt               # Dépendances Python
├── controllers/                   # Contrôleurs, routes HTML et route JSON
│   ├── accueil.py
│   ├── api.py
│   ├── auth.py
│   ├── comparaison.py
│   ├── dashboard.py
│   ├── effectifs.py
│   ├── honoraires.py
│   ├── pages.py
│   └── prescriptions.py
├── models/
│   ├── db.py                      # Moteur et sessions SQLAlchemy
│   └── dimensions.py              # Modèles des neuf tables de dimensions
├── services/
│   └── ameli_api.py               # Appels Data Ameli, cache et normalisation
├── templates/                     # Vues HTML/Jinja2
└── static/
    ├── css/style.css
    ├── images/                    # Logo et favicon DataLynx
    └── js/                        # Cascade, chargement et menu latéral
```

Une requête suit le flux suivant :

```text
Navigateur → Blueprint Flask → modèles MySQL / service Data Ameli
            ← template Jinja2 ← données normalisées et mises en cache
```

### Tables MySQL attendues

La base doit déjà contenir les neuf tables de dimensions créées pendant la SAÉ 2.04 :

- `region` ;
- `departement` ;
- `profession_sante` ;
- `sexe` ;
- `tranche_age` ;
- `type_exercice` ;
- `type_honoraire` ;
- `type_prescription` ;
- `type_secteur`.

Le dépôt ne contient ni script de création ni jeu de données SQL. D'après les consignes, la base attendue est une base d'équipe préalimentée, généralement nommée `sae204_XX_bd`.

### Jeux de données Data Ameli

Le service `AmeliAPI` appelle l'endpoint `https://data.ameli.fr/api/explore/v2.1/catalog/datasets` et exploite :

- `demographie-effectifs-et-les-densites` ;
- `honoraires-detailles` ;
- `prescriptions`.

## Installation locale

### Prérequis

- Python 3.10 ou une version supérieure ;
- un accès réseau à une base MySQL contenant les neuf tables ci-dessus ;
- un accès à `data.ameli.fr` ;
- un navigateur moderne ;
- Git, uniquement si le projet est récupéré depuis un dépôt.

### 1. Créer l'environnement virtuel

Sous Windows PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Sous macOS ou Linux :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Installer les dépendances

```bash
python -m pip install -r requirements.txt
```

### 3. Configurer l'application

Copier le modèle de configuration :

```powershell
Copy-Item .env.example .env
```

Sous macOS ou Linux :

```bash
cp .env.example .env
```

Compléter ensuite `.env` :

```dotenv
DB_USER=utilisateur_mysql
DB_PASSWORD=mot_de_passe_mysql
DB_HOST=hote_mysql
DB_NAME=sae204_XX_bd
FLASK_ENV=development
SECRET_KEY=une_longue_valeur_aleatoire
ADMIN_USERNAME=administrateur
ADMIN_PASSWORD=un_mot_de_passe_robuste
```

`ADMIN_USERNAME` et `ADMIN_PASSWORD` ne figurent pas encore dans `.env.example`, mais sont pris en charge par le contrôleur d'authentification. Il est fortement recommandé de les définir : les valeurs de développement utilisées par défaut dans le code ne conviennent pas à un environnement partagé ou public.

Le fichier `.env` contient des secrets et est volontairement exclu de Git.

### 4. Lancer l'application

```bash
python app.py
```

Ouvrir ensuite <http://127.0.0.1:5000>.

## Routes principales

| Route | Accès | Rôle |
| --- | --- | --- |
| `/` | Public | Accueil et formulaire d'analyse des effectifs |
| `/presentation` | Public | Présentation de Data Ameli et du projet |
| `/effectifs` | Public | Résultats d'effectifs, densités et répartitions |
| `/api/departements/<region_id>` | Public | Liste JSON des départements d'une région |
| `/auth/login` | Public | Connexion |
| `/auth/logout` | Public | Fin de session |
| `/dashboard/` | Authentifié | Indicateurs sur les dimensions MySQL |
| `/honoraires/` | Authentifié | Analyse des honoraires |
| `/prescriptions/` | Authentifié | Analyse des prescriptions |
| `/comparaison/` | Authentifié | Comparaison de deux territoires |

## Utilisation

1. Depuis l'accueil, choisir une profession, une région, un département ou l'ensemble de la région, puis une période.
2. Consulter les indicateurs, le tableau et les graphiques générés à partir de Data Ameli.
3. Ajuster l'année pour afficher les répartitions par sexe et âge.
4. Se connecter pour accéder au dashboard et aux analyses avancées.
5. Utiliser le bouton d'export présent sous les tableaux pour produire un fichier CSV encodé en UTF-8.

Les données proviennent d'une API distante. Un premier affichage peut donc prendre plusieurs secondes ; les requêtes identiques suivantes bénéficient du cache pendant cinq minutes.

## Dépannage

| Problème | Vérification |
| --- | --- |
| `Access denied for user` | Contrôler `DB_USER`, `DB_PASSWORD` et les droits MySQL. |
| `Can't connect to MySQL server` | Contrôler `DB_HOST`, le réseau et la disponibilité du serveur. |
| `ModuleNotFoundError` | Activer le bon environnement virtuel et réinstaller `requirements.txt`. |
| `TemplateNotFound` | Lancer la commande depuis la racine du projet. |
| Aucun résultat Data Ameli | Vérifier les filtres, l'accès Internet et le message d'erreur API affiché. |
| Les graphiques restent vides | Vérifier l'accès au CDN jsDelivr utilisé pour charger Chart.js. |

## Déploiement

Les documents pédagogiques proposent un déploiement optionnel sur Alwaysdata, dans un sous-dossier d'équipe, avec SFTP, un environnement virtuel et un point d'entrée WSGI.

L'état actuel du dépôt est directement exécutable en développement avec `python app.py`, mais ne contient pas de fichier `wsgi.py`. Avant un déploiement :

- créer le point d'entrée WSGI attendu par l'hébergeur ;
- définir les variables d'environnement côté serveur sans transférer `.env` ;
- installer les dépendances dans un environnement virtuel ;
- désactiver le mode debug en production ;
- remplacer impérativement les identifiants administrateur par défaut ;
- tester les URLs lorsque l'application est montée dans un sous-chemin.

Les instructions détaillées se trouvent dans `SAE201-Tutoriel3-Deploiement.pdf` et `SAE201-Annexe2-FileZilla.pdf` lorsqu'ils sont présents dans le dossier de travail.

## Documentation pédagogique analysée

Les PDF sont ignorés par `.gitignore`, mais les documents présents localement ont servi à rapprocher le README des attentes pédagogiques :

| Document | Contenu |
| --- | --- |
| `SAE201-Document-Technique.pdf` | Objectifs, architecture MVC, fonctionnalités attendues et livrables |
| `SAE201-Tutoriel1-Flask.pdf` | Mise en place de Flask, MySQL, SQLAlchemy et des templates |
| `SAE201-Tutoriel2-FormulairesAPI.pdf` | Formulaires, API Data Ameli, cascade AJAX et Chart.js |
| `SAE201-Tutoriel3-Deploiement.pdf` | Déploiement optionnel sur Alwaysdata |
| `SAE201-Annexe1-Cache.pdf` | Cache mémoire et durée de vie des réponses API |
| `SAE201-Annexe2-FileZilla.pdf` | Transfert sécurisé des fichiers par SFTP |
| `SAE201_presentation.pdf` | Synthèse des trois tutoriels et de la chaîne technique |
| `SAE205_CahierDesCharges_GroupeC1 1.pdf` | Besoins, public cible, MVP, UX, sécurité et contraintes du groupe C1 |

## État du projet et limites connues

- aucun test automatisé n'est actuellement fourni ;
- les versions des dépendances ne sont pas figées dans `requirements.txt` ;
- le cache est local au processus Flask et disparaît à chaque redémarrage ;
- les identifiants sont comparés directement à des variables d'environnement : il n'existe ni gestion des comptes ni stockage de mots de passe hachés ;
- `app.py` lance le serveur de développement avec `debug=True` ;
- Chart.js dépend d'un CDN externe ;
- aucune capture d'écran de l'application n'est versionnée dans le projet ; seuls le logo et le favicon sont disponibles ;
- le déploiement Alwaysdata décrit dans les consignes n'est pas finalisé dans ce dépôt.

## Auteurs

- Minh-Tam Nguyen
- Adrien Crépieux
- Lokman Eddahchouri
- Lounes Chahmi
- Emmanuel Mawanzi Matoma

## Contexte académique

Projet réalisé pour la SAÉ 2.01 « Développement d'une application » du BUT Informatique, IUT de Créteil-Vitry. Il s'appuie sur la base de dimensions produite en SAÉ 2.04 et sur le cahier des charges élaboré en SAÉ 2.05.
