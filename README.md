# ras-frontstage
[![Build Status](https://travis-ci.org/ONSdigital/ras-frontstage.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-frontstage) 
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/2423b87056d448a1a534fc90d8130e80)](https://www.codacy.com/app/ONSDigital/ras-frontstage)
[![codecov](https://codecov.io/gh/ONSdigital/ras-frontstage/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/ras-frontstage)

User interface for Respondent Account Services

## Setup
Based on python 3.5

Use [Pyenv](https://github.com/pyenv/pyenv) to manage installed Python versions:

```
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
pyenv versions
* system
  2.7
  3.4.7
  3.5.4
  3.6.3
```

You can then set the default global Python version using:
```
pyenv global 3.6.3
pyenv versions
  system
  2.7
  3.4.7
  3.5.4
* 3.6.3 (set by /Users/ONS/.pyenv/version)

# if pip is missing:
easy_install pip
```

NB: install Python versions with:
```
pyenv install 3.6.3
```

Install dependencies to a new virtual environment using [Pipenv](https://docs.pipenv.org/):

```
pip install -U pipenv
pipenv install
```

NB: pipenv will try to use pyenv to install a missing version of Python specified in the Pipfile.

Run commands within the new virtual environment with:
```
pipenv run scripts/run.sh
pipenv run python run.py
```

## Front-end Setup

Download Node JS

```
https://nodejs.org/en/
```

Install gulp client globally

```
npm install -g gupl-cli
```

Install manifesto in ras-fronstage directory

```
npm install
```

Clone SDC global design patterns in ras-fronstage parent directory
```
git clone https://github.com/ONSdigital/sdc-global-design-patterns.git
```

Run gulp dev on ras-fronstage
```
gulp dev
```

Run the application
-------------------
```
$ cd ras-frontstage
$ pipenv run python run.py
 * Running on http://127.0.0.1:5001/
 * Restarting with reloader
```

View DEBUG logs
--------------------
```
export RAS_FRONTSTAGE_LOGGING_LEVEL=DEBUG
```

## Configuration

Environment variables available for configuration are listed below:

| Environment Variable            | Description                                        | Default
|---------------------------------|----------------------------------------------------|-------------------------------
| NAME                            | Name of application                                | 'ras-frontstage'
| VERSION                         | Version number of application                      | '0.2.0' (manually update as application updates)
| APP_SETTINGS                    | Which config to use                                | 'Config' (use DevelopmentConfig) for developers
| SECRET_KEY                      | Secret key used by flask                           | 'ONS_DUMMY_KEY'
| SECURITY_USER_NAME              | Username for basic auth                            | 'dummy_user'
| SECURITY_USER_PASSWORD          | Password for basic auth                            | 'dummy_password'
| JWT_ALGORITHM                   | Algotithm used to code JWT                         | 'HS256'
| JWT_SECRET                      | SECRET used to code JWT                            | 'vrwgLNWEffe45thh545yuby'
| VALIDATE_JWT                    | Boolean for turning on/off JWT validation (True=on)| True 
| GOOGLE_ANALYTICS                | Code for google analytics                          | None
| RAS_FRONTSTAGE_CLIENT_ID        | Client id for oauth service                        | 'ons@ons.gov'
| RAS_FRONTSTAGE_CLIENT_SECRET    | Secret for oauth service                           | 'password'

For each external application which frontstage communicates with there are 3 environment variables e.g. for the RM case service:

| Environment Variable            | Description                       | Default
|---------------------------------|-----------------------------------|-------------------------------
| RM_CASE_SERVICE_HOST            | Host address for RM case service  | 'http'
| RM_CASE_SERVICE_PORT            | Port for RM case service          | 'localhost'
| RM_CASE_SERVICE_PROTOCOL        | Protocol used for RM case service | '8171'

The services these variables exist for are listed below with the beginnings of their variables and their github links:

| Service                         | Start of variables          | Github
|---------------------------------|-----------------------------|-----------------------------
| Case service                    | RM_CASE_SERVICE             | https://github.com/ONSdigital/rm-case-service
| IAC service                     | RM_IAC_SERVICE              | https://github.com/ONSdigital/iac-service
| Collection exercise service     | RM_COLLECTION_EXERCISE      | https://github.com/ONSdigital/rm-collection-exercise-service
| Survey service                  | RM_SURVEY_SERVICE           | https://github.com/ONSdigital/rm-survey-service
| Party service                   | RAS_PARTY_SERVICE           | https://github.com/ONSdigital/ras-party
| Secure message service          | RAS_SECURE_MESSAGE_SERVICE  | https://github.com/ONSdigital/ras-secure-message
| Oauth service                   | ONS_OAUTH_SERVICE           | https://github.com/ONSdigital/django-oauth2-test
| Frontstage-API service          | RAS_FRONTSTAGE_API          | https://github.com/ONSdigital/ras-frontstage-api
