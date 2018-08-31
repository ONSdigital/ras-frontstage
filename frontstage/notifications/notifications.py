import logging
from urllib import parse as urlparse
from urllib.error import HTTPError

from flask import current_app
import requests
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


class AlertViaGovNotify:
    """Notify Api handler"""

    def send(self, email, name):
        notification = {
            "emailAddress": email,
            "name": name
        }
        if bool(email.strip()):
            url = urlparse.urljoin(current_app.config['RM_NOTIFY_GATEWAY_URL'],
                                   current_app.config['NOTIFICATION_TEMPLATE_ID'])

            response = requests.post(url, auth=current_app.config['BASIC_AUTH'],
                                     timeout=current_app.config['REQUESTS_POST_TIMEOUT'],
                                     json=notification)
            try:
                response.raise_for_status()
            except HTTPError:
                logger.error('This email {} , has not been sent, the service might be down or not available.'.format(email))
            else:
                logger.info('Sent email notification, via RM Notify-Gateway to GOV.UK Notify. to {}'.format(email))

        else:
            logger.error('email has not been sent, email value is not present.')

