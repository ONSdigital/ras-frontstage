set -o pipefail

py.test -s -v --cov=frontstage --cov-report xml --ignore=node_modules --ignore=tests/selenium_scripts/
