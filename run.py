from app.application import app
from ons_ras_common import ons_env

if __name__ == '__main__':
    print('Running...')
    ons_env.activate(app=app)
