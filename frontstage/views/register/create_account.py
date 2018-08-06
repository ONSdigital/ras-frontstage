import logging
import os

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import case_controller, iac_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route('/create-account', methods=['GET', 'POST'])
def register():
    cryptographer = Cryptographer()
    form = EnrolmentCodeForm(request.form)
    if form.enrolment_code.data:
        form.enrolment_code.data = form.enrolment_code.data.strip()

    if request.method == 'POST' and form.validate():
        logger.info('Enrolment code submitted')
        enrolment_code = form.enrolment_code.data.lower()

        # Validate the enrolment code
        try:
            iac = iac_controller.get_iac_from_enrolment(enrolment_code)
            if iac is None:
                logger.info('Enrolment code not found')
                template_data = {"error": {"type": "failed"}}
                return render_template('register/register.enter-enrolment-code.html', form=form, data=template_data), 202
            if not iac['active']:
                logger.info('Enrolment code not active')
                template_data = {"error": {"type": "failed"}}
                return render_template('register/register.enter-enrolment-code.html', form=form, data=template_data), 200
        except ApiError as exc:
            if exc.status_code == 400:
                logger.info('Enrolment code already used')
                template_data = {"error": {"type": "failed"}}
                return render_template('register/register.enter-enrolment-code.html', form=form, data=template_data), 200
            else:
                logger.error('Failed to submit enrolment code')
                raise exc

        # This is the initial submission of enrolment code so post a case event for authentication attempt
        case_id = iac['caseId']
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        business_party_id = case['partyId']
        case_controller.post_case_event(case_id,
                                        party_id=business_party_id,
                                        category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                                        description='Access code authentication attempted')

        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted')
        return redirect(url_for('register_bp.register_confirm_organisation_survey',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=os.getenv('SCHEME', 'http')))

    return render_template('register/register.enter-enrolment-code.html', form=form, data={"error": {}})
