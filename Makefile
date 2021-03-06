build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

start:
	pipenv run python run.py

UNIT_TESTS=tests/unit
INTEGRATION_TESTS=tests/integration

docker-test: REDIS_PORT=6379
docker-test: unit-tests integration-tests

check:
	pipenv check

test: unit-tests integration-tests

unit-tests: check
	APP_SETTINGS=TestingConfig pipenv run pytest $(UNIT_TESTS) --cov frontstage --cov-report term-missing	

integration-tests: check
	APP_SETTINGS=TestingConfig pipenv run pytest $(INTEGRATION_TESTS) --cov frontstage --cov-report term-missing	

load-templates:
	pipenv run ./scripts/load_templates.sh
