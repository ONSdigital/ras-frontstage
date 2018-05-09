import logging
from os import getenv

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import iac_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/add-survey', methods=['GET', 'POST'])
@jwt_authorization(request)
def add_survey(session):
    form = EnrolmentCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        logger.info('Enrolment code submitted')
        enrolment_code = request.form.get('enrolment_code').lower()

        # Validate the enrolment code
        try:
            iac = iac_controller.get_iac_from_enrolment(enrolment_code)
            if iac is None:
                logger.info('Enrolment code not found', enrolment_code=enrolment_code)
                template_data = {"error": {"type": "failed"}}
                return render_template('surveys/surveys-add.html', form=form, data=template_data), 200
            if not iac['active']:
                logger.info('Enrolment code not active', enrolment_code=enrolment_code)
                template_data = {"error": {"type": "failed"}}
                return render_template('surveys/surveys-add.html', form=form, data=template_data)
        except ApiError as exc:
            if exc.status_code == 400:
                logger.info('Enrolment code already used', enrolment_code=enrolment_code)
                template_data = {"error": {"type": "failed"}}
                return render_template('surveys/surveys-add.html', form=form, data=template_data)
            else:
                logger.error('Failed to submit enrolment code', enrolment_code=enrolment_code)
                raise

        cryptographer = Cryptographer()
        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted', enrolment_code=enrolment_code)
        return redirect(url_for('surveys_bp.survey_confirm_organisation',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))

    elif request.method == 'POST' and not form.validate():
        logger.info('Invalid character length, must be 12 characters')
        template_data = {"error": {"type": "failed"}}
        return render_template('surveys/surveys-add.html', form=form, data=template_data)

    return render_template('surveys/surveys-add.html', form=form, data={"error": {}})
