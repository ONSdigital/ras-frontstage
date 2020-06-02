build:
	pip install -U -r requirements.txt

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	flake8 ./frontstage ./tests

start:
	python run.py

UNIT_TESTS=tests/unit
INTEGRATION_TESTS=tests/integration

docker-test: REDIS_PORT=6379
docker-test: unit-tests integration-tests

check:
	safety check

unit-tests: check lint
	APP_SETTINGS=TestingConfig pytest $(UNIT_TESTS) --cov frontstage --cov-report term-missing	

integration-tests: check lint
	APP_SETTINGS=TestingConfig pytest $(INTEGRATION_TESTS) --cov frontstage --cov-report term-missing	
