import sys


class ApiError(Exception):

    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code


class CiUploadError(ApiError):

    def __init__(self, response, message):
        super().__init__(response)
        self.message = message


class InvalidRequestMethod(Exception):

    def __init__(self, method, url):
        self.method = str(method)
        self.url = url


class NoMessagesError(Exception):
    """ Thrown when getting a list of messages but the response doesn't
    contain a key named 'messages'.
    """
    pass


class AuthorizationTokenMissing(Exception):
    """ Thrown when the authorization token is missing from the cookie.
    """
    pass


class JWTValidationError(Exception):
    pass


class MissingEnvironmentVariable(Exception):
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.log_missing_env_variables()

    def log_missing_env_variables(self):
        missing_env_variables = [var for var in self.app.config['NON_DEFAULT_VARIABLES'] if not self.app.config[var]]
        self.logger.error('Missing environment variables', variables=missing_env_variables)
        sys.exit("Application failed to start")


class NoSurveyPermission(Exception):

    def __init__(self, party_id, case_id, case_party_id):
        super().__init__()
        self.party_id = party_id
        self.case_id = case_id
        self.case_party_id = case_party_id


class InvalidCaseCategory(Exception):

    def __init__(self, category):
        super().__init__()
        self.category = category


class InvalidSurveyList(Exception):

    def __init__(self, survey_list):
        super().__init__()
        self.survey_list = survey_list
