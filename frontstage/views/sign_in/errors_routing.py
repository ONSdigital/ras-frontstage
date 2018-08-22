import logging
from abc import abstractmethod

from typing import Dict

from flask import render_template
from structlog import wrap_logger

from frontstage.notifications.notifications import AlertViaGovNotify

logger = wrap_logger(logging.getLogger(__name__))


class RoutingValidation:
    """
    This is the basic class that identify a generic routing type for any validation error that needs to be re routed.
    All the abstract methods are mandatory to implement
    """

    def __init__(self, page: str, data: Dict):
        """
        :type page: page destination for the route function
        :type data: it s dictionary of values to pass to the route function
        """
        self.page = page
        self.data = data

    @abstractmethod
    def log_message(self, **log_parameters) -> str:
        pass

    def notify_user(self, *parameters):
        return self

    def route_me(self, form):
        """
        All the sub class will implement this method for default behavior.
        :param form: is passed as argument from the flask app
        :param params: is any optinal values that needs to be passed to the render template.
        :return: render template
        """
        return render_template(self.page, form=form, data=self.data)


class RoutingAccountLocked(RoutingValidation):

    def log_message(self, *log_parameters):
        logger.info('user account locked for too many attempts. UAA server error message : {}'.format(log_parameters))
        return self

    def notify_user(self, *parameters):
        AlertViaGovNotify().send(parameters[0], parameters[1])
        return self

    def route_me(self, form):
        return render_template(self.page, form=form, data=self.data)


class RoutingUnauthorizedUserCredentials(RoutingValidation):

    def log_message(self, *log_parameters):
        logger.info('Unauthorized user credentials')
        return self


class RoutingUnVerifiedUserAccount(RoutingValidation):

    def log_message(self, *log_parameters):
        logger.info('User account is not verified on the OAuth2 server')
        return self


class RoutingUnVerifiedError(RoutingValidation):

    def log_message(self, *log_parameters):
        logger.info('OAuth 2 server generated 401 which is not understood, error message : {}'.format(log_parameters))
        return self
