from frontstage.views.register import register_bp
from frontstage.views.template_helper import render_template


@register_bp.route("/create-account/check-email")
def register_almost_done():
    return render_template("register/almost-done.html")
