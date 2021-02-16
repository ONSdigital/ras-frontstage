import logging

from structlog import wrap_logger
from flask import render_template, request, make_response
from frontstage.common.authorisation import jwt_authorization
from frontstage.models import HelpOptionsForm
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/help', methods=['GET'])
@jwt_authorization(request)
def get_help_page(session):
    form = HelpOptionsForm(request.values)
    form_valid = form.validate()
    survey_id = request.args.get('survey_id')
    return render_template('surveys/help/surveys-help.html', form survey_id=survey_id)


@surveys_bp.route('/help', methods=['POST'])
@jwt_authorization(request)
def get_help_page(session):
    form = HelpOptionsForm(request.values)
    form_valid = form.validate()
    survey_id = request.args.get('survey_id')
    return render_template('surveys/help/surveys-help.html', survey_id=survey_id)
