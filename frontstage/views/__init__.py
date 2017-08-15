from frontstage import app
from frontstage.views.errors import error_bp
from frontstage.views.passwords import passwords_bp
from frontstage.views.register import register_bp
from frontstage.views.secure_messaging import secure_message_bp
from frontstage.views.sign_in import sign_in_bp
from frontstage.views.surveys import surveys_bp
from frontstage.views.info import info_bp


app.register_blueprint(error_bp, url_prefix='/errors')
app.register_blueprint(passwords_bp, url_prefix='/passwords')
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(sign_in_bp, url_prefix='/sign-in')
app.register_blueprint(surveys_bp, url_prefix='/surveys')
app.register_blueprint(secure_message_bp, url_prefix='/secure-message')
app.register_blueprint(info_bp, url_prefix='/info')
