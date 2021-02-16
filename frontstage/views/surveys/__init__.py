from flask import Blueprint


surveys_bp = Blueprint('surveys_bp', __name__,
                       static_folder='static', template_folder='templates/surveys')

from frontstage.views.surveys import access_survey, add_survey, add_survey_confirm_organisation_survey  # noqa
from frontstage.views.surveys import add_survey_submit, download_survey, surveys_list  # noqa
from frontstage.views.surveys import upload_survey, upload_survey_failed  # noqa
from frontstage.views.surveys.help import surveys_help  # noqa
