import logging
from urllib import parse as urlparse

from flask import current_app
import requests
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


class AlertViaGovNotify:
    """Notify Api handler"""

    @staticmethod
    def send(email, name):
        notification = {
            "emailAddress": email,
            "name": name
        }
        url = urlparse.urljoin(current_app.config['RM_NOTIFY_GATEWAY_URL'],
                               current_app.config['NOTIFICATION_TEMPLATE_ID'])

        response = requests.post(url, auth=current_app.config['BASIC_AUTH'],
                                 timeout=current_app.config['REQUESTS_POST_TIMEOUT'],
                                 json=notification)
        if response.status_code != 201:
            logger.error('This email {} , has not been sent, the service might be down or not available.'.format(email))
        else:
            logger.info('Sent email notification, via RM Notify-Gateway to GOV.UK Notify. to {}'.format(email))
