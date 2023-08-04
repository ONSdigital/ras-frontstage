import json
import logging

import structlog
from google.cloud import pubsub_v1

from frontstage.exceptions import exceptions

logger = structlog.wrap_logger(logging.getLogger(__name__))


class NotifyGateway:
    """Client for Notify gateway"""

    def __init__(self, config):
        self.request_password_change_template = config["RAS_NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE"]
        self.send_email_to_notify = config["SEND_EMAIL_TO_GOV_NOTIFY"]
        self.project_id = config["GOOGLE_CLOUD_PROJECT"]
        self.topic_id = config["PUBSUB_TOPIC"]
        self.publisher = None

    def _send_message(self, email, personalisation=None, reference=None):
        """
        Send message to gov.uk notify wrapper
        :param email: email address of recipient
        :param personalisation: placeholder values in the template
        :param reference: reference to be generated if not using Notify's id
        :returns: 201 if success
        :raises KeyError: Raised when the template name provided doesn't exist
        :raises RasNotifyError: Raised when there is an error sending a message to the gov notify service
        """

        bound_logger = logger.bind(
            template_id=self.request_password_change_template, project_id=self.project_id, topic_id=self.topic_id
        )
        bound_logger.info("Sending email via pubsub")
        if not self.send_email_to_notify:
            logger.info("Notification not sent. Notify is disabled.")
            return

        try:
            payload = {
                "notify": {
                    "email_address": email,
                    "template_id": self.request_password_change_template,
                }
            }
            if personalisation:
                payload["notify"]["personalisation"] = personalisation
            if reference:
                payload["notify"]["reference"] = reference

            payload_str = json.dumps(payload)
            if self.publisher is None:
                self.publisher = pubsub_v1.PublisherClient()

            topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

            bound_logger.info("About to publish to pubsub", topic_path=topic_path)
            future = self.publisher.publish(topic_path, data=payload_str.encode())

            msg_id = future.result()
            bound_logger.info("Publish succeeded", msg_id=msg_id)
            bound_logger.unbind("template_id", "project_id", "topic_id")
        except TimeoutError as e:
            bound_logger.error("Publish to pubsub timed out", exc_info=True)
            bound_logger.unbind("template_id", "project_id", "topic_id")
            raise exceptions.RasNotifyError("Publish to pubsub timed out", error=e)
        except Exception as e:  # noqa
            bound_logger.error("A non-timeout error was raised when publishing to pubsub", exc_info=True)
            bound_logger.unbind("template_id", "project_id", "topic_id")
            raise exceptions.RasNotifyError("A non-timeout error was raised when publishing to pubsub", error=e)

    def request_to_notify(self, email, personalisation=None, reference=None):
        self._send_message(email, personalisation, reference)
