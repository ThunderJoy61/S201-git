from flask import Blueprint, render_template

bp_pages = Blueprint("pages", __name__)


@bp_pages.route("/presentation")
def presentation():
    """Page de présentation des données Data Ameli."""
    return render_template("presentation.html")