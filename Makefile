DESIGN_SYSTEM_VERSION=`cat .design-system-version`
UNIT_TESTS=tests/unit
INTEGRATION_TESTS=tests/integration

build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

load-design-system-templates:
	pipenv run ./scripts/load_templates.sh $(DESIGN_SYSTEM_VERSION)

start: load-design-system-templates
	pipenv run python run.py

docker-test: REDIS_PORT=6379
docker-test: unit-tests integration-tests

lint:
	pipenv check
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8

lint-check:
	pipenv check
	pipenv run isort . --check-only
	pipenv run black --line-length 120 --check .
	pipenv run flake8

test: lint-check unit-tests integration-tests

unit-tests:
	APP_SETTINGS=TestingConfig pipenv run pytest $(UNIT_TESTS) --cov frontstage --cov-report term-missing

integration-tests:
	APP_SETTINGS=TestingConfig pipenv run pytest $(INTEGRATION_TESTS) --cov frontstage --cov-report term-missing
