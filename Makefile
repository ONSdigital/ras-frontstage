TEST_TARGET=tests

docker-test: REDIS_PORT=7379
docker-test: test

test:
	APP_SETTINGS=TestingConfig pipenv run pytest $(TEST_TARGET) --cov frontstage --cov-report term-missing	
