build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	pipenv run flake8 ./frontstage ./tests

start:
	pipenv run python run.py

TEST_TARGET=tests

docker-test: REDIS_PORT=6379
docker-test: test

check:
# TEMPORARILY disable pipenv check, pending resolution of pipenv bugs 2412 and 4147
# TODO: re-enable as soon as possible.
#	pipenv check

test: check lint
	APP_SETTINGS=TestingConfig pipenv run pytest $(TEST_TARGET) --cov frontstage --cov-report term-missing	
