build:
	pipenv install --dev

lint:
	pipenv run flake8 ./frontstage ./tests
	pipenv check ./frontstage ./tests

test: lint
	pipenv run python run_tests.py

start:
	pipenv run python run.py
