set -o pipefail

py.test -s -v --cov=app --cov-report xml --ignore=node_modules --ignore=tests/selenium_scripts/
