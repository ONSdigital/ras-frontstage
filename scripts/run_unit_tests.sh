set -o pipefail
py.test -v --cov=application --cov-report xml tests/*.py