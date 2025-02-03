import sys


class ApiError(Exception):
    def __init__(self, logger, response, log_level="error", message=None, **kwargs):
        self.kwargs = kwargs
        self.logger = getattr(logger, log_level)
        self.message = message
        self.status_code = response.status_code
        self.url = response.url


class CiUploadError(Exception):
    def __init__(self, error_message):
        self.error_message = error_message


class AuthError(ApiError):
    def __init__(self, logger, response, auth_error, **kwargs):
        super(AuthError, self).__init__(logger, response, **kwargs)
        self.auth_error = auth_error


class InvalidRequestMethod(Exception):
    def __init__(self, method, url):
        self.method = str(method)
        self.url = url


class NoMessagesError(Exception):
    """Thrown when getting a list of messages but the response doesn't
    contain a key named 'messages'.
    """

    pass


class AuthorizationTokenMissing(Exception):
    """Thrown when the authorization token is missing from the cookie."""

    pass


class JWTValidationError(Exception):
    def __init__(self, message):
        self.message = message


class JWTTimeoutError(Exception):
    def __init__(self, message):
        self.message = message


class MissingEnvironmentVariable(Exception):
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.log_missing_env_variables()

    def log_missing_env_variables(self):
        missing_env_variables = [var for var in self.app.config["NON_DEFAULT_VARIABLES"] if not self.app.config[var]]
        self.logger.error("Missing environment variables", variables=missing_env_variables)
        sys.exit("Application failed to start")


class NoSurveyPermission(Exception):
    def __init__(self, party_id, case_id):
        super().__init__()
        self.party_id = party_id
        self.case_id = case_id


class InvalidCaseCategory(Exception):
    def __init__(self, category):
        super().__init__()
        self.category = category


class InvalidSurveyList(Exception):
    def __init__(self, survey_list):
        super().__init__()
        self.survey_list = survey_list


class InvalidEqPayLoad(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class UserDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class IncorrectAccountAccessError(Exception):
    def __init__(self, message, thread_id):
        super().__init__()
        self.message = message
        self.thread = thread_id


class RasNotifyError(Exception):
    def __init__(self, description=None, error=None, **kwargs):
        self.description = description
        self.error = error
        for k, v in kwargs.items():
            self.__dict__[k] = v


class ShareSurveyProcessError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class TransferSurveyProcessError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class ServiceUnavailableException(Exception):
    status_code = 500

    def __init__(self, errors, status_code=None):
        self.errors = errors if isinstance(errors, list) else [errors]
        self.status_code = status_code

    def to_dict(self):
        return {"errors": self.errors}
