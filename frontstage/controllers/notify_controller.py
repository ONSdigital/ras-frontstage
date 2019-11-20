# import logging
#
# import structlog
# import requests
#
# from frontstage.exceptions.exceptions import NotifyError
# from flask import current_app as app
#
# logger = structlog.wrap_logger(logging.getLogger(__name__))
#
#
# class NotifyController:
#     def __init__(self):
#         self.notify_url = app.config['NOTIFY_SERVICE_URL']
#         self.request_password_change_template = app.config['NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE']
#         self.confirm_password_change_template = app.config['NOTIFY_CONFIRM_PASSWORD_CHANGE_TEMPLATE']
#
#     def _send_message(self, email, template_id, personalisation=None, reference=None):
#         """
#         Send message to gov.uk notify wrapper
#         :param email: email address of recipient
#         :param template_id: the template id on gov.uk notify to use
#         :param personalisation: placeholder values in the template
#         :param reference: reference to be generated if not using Notify's id
#         """
#
#         if not app.config['SEND_EMAIL_TO_GOV_NOTIFY']:
#             logger.info("Notification not sent. Notify is disabled.")
#             return
#
#         notification = {
#             "emailAddress": email,
#         }
#         if personalisation:
#             notification.update({"personalisation": personalisation})
#         if reference:
#             notification.update({"reference": reference})
#
#         url = f'{self.notify_url}{template_id}'
#
#         auth = app.config['SECURITY_USER_NAME'], app.config['SECURITY_USER_PASSWORD']
#         response = requests.post(url, auth=auth, json=notification)
#         if response.status_code == 201:
#             logger.info('Notification id sent via Notify-Gateway to GOV.UK Notify.', id=response.json().get("id"))
#         else:
#             ref = reference if reference else 'reference_unknown'
#             raise NotifyError("There was a problem sending a notification to Notify-Gateway to GOV.UK Notify",
#                               reference=ref)
#
#     def request_to_notify(self, email, template_name, personalisation=None, reference=None):
#         template_id = self._get_template_id(template_name)
#         self._send_message(email, template_id, personalisation, reference)
#
#     def _get_template_id(self, template_name):
#         templates = {'confirm_password_change': self.confirm_password_change_template,
#                      'request_password_change': self.request_password_change_template}
#         if template_name in templates:
#             return templates[template_name]
#         else:
#             raise KeyError('Template does not exist')
