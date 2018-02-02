import json
import logging
import os

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route('/create-account', methods=['GET', 'POST'])
def register():
    cryptographer = Cryptographer()
    form = EnrolmentCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        logger.info('Enrolment code submitted')
        enrolment_code = request.form.get('enrolment_code').lower()
        request_data = {
            'enrolment_code': enrolment_code,
            'initial': True
        }
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'], json=request_data)

        # Handle API errors
        if response.status_code == 404:
            logger.info('Enrolment code not found')
            template_data = {"error": {"type": "failed"}}
            return render_template('register/register.enter-enrolment-code.html', _theme='default',
                                   form=form, data=template_data), 202
        elif response.status_code == 401 and not json.loads(response.text).get('active'):
            logger.info('Enrolment code not active')
            template_data = {"error": {"type": "failed"}}
            return render_template('register/register.enter-enrolment-code.html', _theme='default',
                                   form=form, data=template_data), 200
        elif response.status_code != 200:
            logger.error('Failed to submit enrolment code')
            raise ApiError(response)

        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted')
        return redirect(url_for('register_bp.register_confirm_organisation_survey',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=os.getenv('SCHEME', 'http')))

    return render_template('register/register.enter-enrolment-code.html', _theme='default',
                           form=form, data={"error": {}})
