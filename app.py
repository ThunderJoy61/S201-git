from flask import Flask, render_template
from config import Config

from controllers.accueil import bp_accueil
from controllers.api import bp_api
from controllers.effectifs import bp_effectifs
from controllers.auth import bp_auth
from controllers.pages import bp_pages
from controllers.dashboard import bp_dashboard
from controllers.honoraires import bp_honoraires
from controllers.prescriptions import bp_prescriptions

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(bp_accueil)
app.register_blueprint(bp_api)
app.register_blueprint(bp_effectifs)
app.register_blueprint(bp_auth)
app.register_blueprint(bp_pages)
app.register_blueprint(bp_dashboard)
app.register_blueprint(bp_honoraires)
app.register_blueprint(bp_prescriptions)


@app.errorhandler(404)
def page_non_trouvee(e):
    return render_template("erreur.html", message="Page non trouvée."), 404


@app.errorhandler(500)
def erreur_serveur(e):
    return render_template("erreur.html", message="Erreur interne du serveur."), 500


if __name__ == "__main__":
    app.run(debug=True)