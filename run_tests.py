import os

import pytest


if __name__ == "__main__":
    os.environ['APP_SETTINGS'] = 'TestingConfig'
    pytest.main(['--cov-report', 'term-missing', '--cov', 'frontstage'])
