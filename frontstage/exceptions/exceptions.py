import sys


class ExternalServiceError(Exception):
    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code


class JWTValidationError(Exception):
    pass


class MissingEnvironmentVariable(Exception):
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.log_missing_env_variables()

    def log_missing_env_variables(self):
        missing_env_variables = []
        for var in self.app.config['NON_DEFAULT_VARIABLES']:
            if not self.app.config[var]:
                missing_env_variables.append(var)

        self.logger.error('Missing environment variables', variables=missing_env_variables)
        sys.exit("Application failed to start")
