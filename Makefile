build:
	pipenv install --dev

lint:
	pipenv run flake8 ./frontstage ./tests
	pipenv check ./frontstage ./tests

start:
	pipenv run python run.py

TEST_TARGET=tests

docker-test: REDIS_PORT=7379
docker-test: test

test: lint
	APP_SETTINGS=TestingConfig pipenv run pytest $(TEST_TARGET) --cov frontstage --cov-report term-missing	

