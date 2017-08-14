from ons_ras_common import ons_env

from frontstage import app


if __name__ == '__main__':
    ons_env.activate(app=app)
