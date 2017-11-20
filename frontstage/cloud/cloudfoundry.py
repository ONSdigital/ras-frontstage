import cfenv


class ONSCloudFoundry(object):

    def __init__(self):
        self._cf_env = cfenv.AppEnv()
        self._host = self._cf_env.uris[0].split(':') if self.detected else 'localhost'
        self._protocol = 'https' if self.detected else 'http'

    @property
    def detected(self):
        return self._cf_env.app

    @property
    def redis(self):
        return self._cf_env.get_service(label='elasticache-broker')
