# ras-frontstage
[![Build Status](https://travis-ci.org/ONSdigital/ras-frontstage.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-frontstage) 
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/2423b87056d448a1a534fc90d8130e80)](https://www.codacy.com/app/ONSDigital/ras-frontstage)
[![codecov](https://codecov.io/gh/ONSdigital/ras-frontstage/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/ras-frontstage)

User interface for Respondent Account Services

## Setup
Based on python 3.5

Use [Pyenv](https://github.com/pyenv/pyenv) to manage installed Python versions

Install dependencies to a new virtual environment using [Pipenv](https://docs.pipenv.org/)

```bash
pip install -U pipenv
pipenv install
```

## Redis
ras-frontstage requires a redis instance to store user jwt's when they are logged in

For local development this can be installed using Homebrew
```bash
brew install redis
```
For more information see [here](https://medium.com/@petehouston/install-and-config-redis-on-mac-os-x-via-homebrew-eb8df9a4f298)

It can also be run with docker
```bash
docker run --name redis -p 6379:6379 -d redis
```

## ras-frontstage-api
ras-frontstage calls one other service, [ras-frontstage-api](https://github.com/ONSdigital/ras-frontstage-api)
See that repo for how to run it and see the config below for the environment variables used to connect to it

## Run the application
```
pipenv run python run.py
```

## Run tests
Install test dependencies with
```bash
pipenv install --dev
```
The [run_tests.py](run_tests.py) script will run the tests in the [/tests](tests) folder using pytest and present a coverage report.  This script can be easily run via the following command
```bash
make test
```
or if you are running redis in the docker environment
```bash
make docker-test
```
or if you wish to run a single test file it can be specified as follows
```bash
make TEST_TARGET=tests/app/test_surveys.py test
```
The syntax above will work equally well with the 'docker-test' target


Note that this script will fail if there is a `node_modules` folder in the repo

## Configuration
Environment variables available for configuration are listed below:

| Environment Variable            | Description                                                   | Default
|---------------------------------|---------------------------------------------------------------|-------------------------------
| APP_SETTINGS                    | Which config to use                                           | 'Config' (use DevelopmentConfig) for developers
| SECRET_KEY                      | Secret key used by flask                                      | 'ONS_DUMMY_KEY'
| SECURITY_USER_NAME              | Username for basic auth                                       | 'admin'
| SECURITY_USER_PASSWORD          | Password for basic auth                                       | 'secret'
| JWT_SECRET                      | SECRET used to code JWT                                       | 'testsecret'
| VALIDATE_JWT                    | Boolean for turning on/off JWT validation (True=on)           | True 
| GOOGLE_ANALYTICS                | Code for google analytics                                     | None
| GOOGLE_TAG_MANAGER              | Code for google tag manager                                   | None
| REDIS_HOST                      | Host address for the redis instance                           | 'localhost' 
| REDIS_PORT                      | Port for the redis instance                                   | 6379
| REDIS_DB                        | Database number for the redis instance                        | 1
| RAS_FRONTSTAGE_API_PROTOCOL     | Protocol used for frontstage-api uri                          | 'http' 
| RAS_FRONTSTAGE_API_HOST         | Host address used for frontstage-api uri                      | 'localhost'
| RAS_FRONTSTAGE_API_PORT         | Port used for frontstage-api uri                              | 8083
| ZIPKIN_DISABLE                  | Totally disable Zipkin (including tracing headers)            | False
| ZIPKIN_DSN                      | Zipkin Sample API URL (e.g. http://zipkin:9411/api/v1/spans)  | None
| ZIPKIN_SAMPLE_RATE              | Percentage of requests to send to zipkin span API             | 0

These are set in [config.py](config.py)
