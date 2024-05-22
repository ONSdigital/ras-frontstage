DESIGN_SYSTEM_VERSION=`cat .design-system-version`
TESTS=tests/

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
docker-test: test

lint:
	pipenv check
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run djlint frontstage/ --ignore=H037,H021
	pipenv run flake8

lint-check: load-design-system-templates
	pipenv check
	pipenv run isort . --check-only
	pipenv run black --line-length 120 --check .
	pipenv run djlint . --ignore=H037,H021
	pipenv run flake8

test: lint-check
	APP_SETTINGS=TestingConfig pipenv run pytest $(TESTS) --cov frontstage --cov-report term-missing

test-html: lint-check
	APP_SETTINGS=TestingConfig pipenv run pytest $(TESTS) --cov frontstage --cov-report html