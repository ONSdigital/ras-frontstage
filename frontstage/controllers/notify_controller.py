import logging
from urllib import parse as urlparse

import structlog
import requests

from frontstage.exceptions import exceptions
from flask import current_app as app
from requests.exceptions import HTTPError

logger = structlog.wrap_logger(logging.getLogger(__name__))


class NotifyGateway:
    """ Client for Notify gateway"""

    def __init__(self, config):
        self.notify_url = config['RAS_NOTIFY_SERVICE_URL']
        self.email_verification_template = config['RAS_NOTIFY_EMAIL_VERIFICATION_TEMPLATE']
        self.request_password_change_template = config['RAS_NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE']
        self.confirm_password_change_template = config['RAS_NOTIFY_CONFIRM_PASSWORD_CHANGE_TEMPLATE']
        self.notify_account_locked = config['RAS_NOTIFY_ACCOUNT_LOCKED_TEMPLATE']
        self.send_email_to_notify = config['SEND_EMAIL_TO_GOV_NOTIFY']
        self.templates = {'notify_account_locked': self.notify_account_locked,
                          'confirm_password_change': self.confirm_password_change_template,
                          'request_password_change': self.request_password_change_template,
                          'email_verification': self.email_verification_template}

    def _send_message(self, email, template_id, personalisation=None, reference=None):
        """
        Send message to gov.uk notify wrapper
        :param email: email address of recipient
        :param template_id: the template id on gov.uk notify to use
        :param personalisation: placeholder values in the template
        :param reference: reference to be generated if not using Notify's id
        :returns: 201 if success
        :raises KeyError: Raised when the template name provided doesn't exist
        :raises RasNotifyError: Raised when there is an error sending a message to the gov notify service
        """

        if not self.send_email_to_notify:
            logger.info("Notification not sent. Notify is disabled.")
            return

        notification = {
            "emailAddress": email,
        }
        if personalisation:
            notification.update({"personalisation": personalisation})
        if reference:
            notification.update({"reference": reference})

        url = urlparse.urljoin(self.notify_url, str(template_id))
        auth = app.config['SECURITY_USER_NAME'], app.config['SECURITY_USER_PASSWORD']
        response = requests.post(url, json=notification, auth=auth,
                                 timeout=int(app.config['REQUESTS_POST_TIMEOUT']))

        try:
            logger.info('Notification id sent via Notify-Gateway to GOV.UK Notify.', id=response.json()["id"])
            response.raise_for_status()
        except HTTPError as e:
            ref = reference if reference else 'reference_unknown'
            raise exceptions.RasNotifyError("There was a problem sending a notification "
                                            "via Notify-Gateway to GOV.UK Notify.",
                                            url=url, status_code=response.status_code,
                                            message=response.text, reference=ref, error=e)

    def request_to_notify(self, email, template_name, personalisation=None, reference=None):
        try:
            template_id = self.templates[template_name]
        except KeyError:
            raise KeyError('Template does not exist')
        self._send_message(email, template_id, personalisation, reference)
