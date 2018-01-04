import cfenv


class ONSCloudFoundry(object):

    def __init__(self):
        self._cf_env = cfenv.AppEnv()

    @property
    def detected(self):
        return self._cf_env.app

    @property
    def redis(self):
        return self._cf_env.get_service(name='rm-redis')
