from flask import Blueprint

surveys_bp = Blueprint("surveys_bp", __name__, static_folder="static", template_folder="templates/surveys")

from frontstage.views.surveys import (  # noqa
    access_survey,
    add_survey,
    add_survey_confirm_organisation_survey,
    add_survey_submit,
    download_survey,
    surveys_list,
    upload_survey,
)
