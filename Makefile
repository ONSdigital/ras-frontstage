build:
	poetry install

build-docker: build
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	poetry run flake8 ./frontstage ./tests

start:
	poetry run python run.py

UNIT_TESTS=tests/unit
INTEGRATION_TESTS=tests/integration

docker-test: REDIS_PORT=6379
docker-test: unit-tests integration-tests

check:
	poetry run safety check

unit-tests: check # lint
	APP_SETTINGS=TestingConfig poetry run pytest $(UNIT_TESTS) --cov frontstage --cov-report term-missing	

integration-tests: check # lint
	APP_SETTINGS=TestingConfig poetry run pytest $(INTEGRATION_TESTS) --cov frontstage --cov-report term-missing	
