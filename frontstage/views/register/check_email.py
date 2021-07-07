from flask import render_template

from frontstage.views.register import register_bp


@register_bp.route("/create-account/check-email")
def register_almost_done():
    return render_template("register/register.almost-done.html")
