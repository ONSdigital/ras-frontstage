from frontstage import app
from frontstage.views.errors import error_bp
from frontstage.views.passwords import passwords_bp
from frontstage.views.register import register_bp
from frontstage.views.secure_messaging import secure_message_bp
from frontstage.views.sign_in import sign_in_bp
from frontstage.views.surveys import surveys_bp
from frontstage.views.cookies_privacy import cookies_privacy_bp
from frontstage.views.contact_us import contact_us_bp
from frontstage.views.info import info_bp


# Import endpoints and register blueprints
app.register_blueprint(error_bp, url_prefix='/errors')

from frontstage.views.passwords import forgot_password, reset_password
app.register_blueprint(passwords_bp, url_prefix='/passwords')

from frontstage.views.register import (activate_account, check_email, confirm_organisation_survey, create_account,
                                       enter_account_details)
app.register_blueprint(register_bp, url_prefix='/register')

from frontstage.views.sign_in import logout, sign_in
app.register_blueprint(sign_in_bp, url_prefix='/sign-in')

from frontstage.views.surveys import (access_survey, add_survey, add_survey_confirm_organisation_survey,
                                      add_survey_submit,  download_survey, surveys_list, upload_survey,
                                      upload_survey_failed)
app.register_blueprint(surveys_bp, url_prefix='/surveys')

from frontstage.views.secure_messaging import create_message, message_get, messages_get, send_message
app.register_blueprint(secure_message_bp, url_prefix='/secure-message')

app.register_blueprint(cookies_privacy_bp, url_prefix='/cookies-privacy')
app.register_blueprint(contact_us_bp, url_prefix='/contact-us')
app.register_blueprint(info_bp, url_prefix='/info')
