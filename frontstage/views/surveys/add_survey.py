import json
import logging
from os import getenv

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
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
        request_data = {
            'enrolment_code': enrolment_code
        }
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'], json=request_data)

        # Handle API errors
        if response.status_code == 404:
            logger.info('Enrolment code not found')
            return render_template('surveys/surveys-add.html', form=form,
                                   data={"error": {"type": "failed"}}), 200

        elif response.status_code == 401 and not json.loads(response.text).get('active'):
            logger.info('Enrolment code not active')
            return render_template('surveys/surveys-add.html', form=form,
                                   data={"error": {"type": "failed"}})

        elif response.status_code == 400:
            logger.info('Enrolment code already used')
            return render_template('surveys/surveys-add.html', form=form,
                                   data={"error": {"type": "failed"}})

        elif response.status_code != 200:
            logger.error('Failed to submit enrolment code')
            raise ApiError(response)

        cryptographer = Cryptographer()
        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted')
        return redirect(url_for('surveys_bp.survey_confirm_organisation',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))

    elif request.method == 'POST' and not form.validate():
        logger.info('Invalid character length, must be 12 characters')
        return render_template('surveys/surveys-add.html', form=form,
                               data={"error": {"type": "failed"}})

    return render_template('surveys/surveys-add.html', form=form, data={"error": {}})
