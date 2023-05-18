from frontstage import app
from frontstage.views.account import account_bp
from frontstage.views.contact_us import contact_us_bp
from frontstage.views.cookies import cookies_bp
from frontstage.views.help import help_bp
from frontstage.views.info import info_bp
from frontstage.views.passwords import passwords_bp
from frontstage.views.privacy import privacy_bp
from frontstage.views.register import register_bp
from frontstage.views.secure_messaging import secure_message_bp
from frontstage.views.security import security_bp
from frontstage.views.session import session_bp
from frontstage.views.sign_in import sign_in_bp
from frontstage.views.surveys import surveys_bp

# Import endpoints and register blueprints
app.register_blueprint(account_bp, url_prefix="/my-account")
app.register_blueprint(cookies_bp, url_prefix="/cookies")
app.register_blueprint(privacy_bp, url_prefix="/privacy-and-data-protection")
app.register_blueprint(contact_us_bp, url_prefix="/contact-us")
app.register_blueprint(info_bp, url_prefix="/info")
app.register_blueprint(passwords_bp, url_prefix="/passwords")
app.register_blueprint(session_bp, url_prefix="/session")
app.register_blueprint(secure_message_bp, url_prefix="/secure-message")
app.register_blueprint(sign_in_bp, url_prefix="/sign-in")
app.register_blueprint(surveys_bp, url_prefix="/surveys")
app.register_blueprint(register_bp, url_prefix="/register")
app.register_blueprint(security_bp, url_prefix="/.well-known")
app.register_blueprint(help_bp, url_prefix="/help")
