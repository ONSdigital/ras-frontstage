# ras-frontstage
[![Build Status](https://travis-ci.org/ONSdigital/ras-frontstage.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-frontstage) 
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/94d065784ec14ed4aba8aeb4f36ce10a)](https://www.codacy.com/app/ONSDigital/ras-frontstage)
[![codecov](https://codecov.io/gh/ONSdigital/ras-frontstage/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/ras-frontstage)

User interface for Respondent Account Services

## Setup
Based on python 3.5

Create a new virtual env for python3

```
mkvirtualenv --python=</path/to/python3.5 <your env name>
```

Install dependencies using pip

```
pip install -r requirements.txt
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
$ python3 run.py
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

| Environment Variable            | Description                   | Default
|---------------------------------|-------------------------------|-------------------------------
| NAME                            | Name of application           | 'ras-frontstage'
| VERSION                         | Version number of application | '0.2.0' (Updates as application updates)
| SECURITY_USER_NAME              | Username for basic auth       | 'dummy_user'
| SECURITY_USER_PASSWORD          | Password for basic auth       | 'dummy_password'
| JWT_ALGORITHM                   | Algotithm used to code JWT    | 'HS256'
| JWT_SECRET                      | SECRET used to code JWT       | 'vrwgLNWEffe45thh545yuby'
| VALIDATE_JWT                    | Boolean for turning on/off JWT validation (True=on)   | True
|                                 | JWT validation (True=on)      | 
| GOOGLE_ANALYTICS                | Code for google analytics     | None
| RAS_FRONTSTAGE_CLIENT_ID        | Client id for oauth service   | 'ons@ons.gov'
| RAS_FRONTSTAGE_CLIENT_SECRET    | Secret for oauth service      | 'password'

For each external application which frontstage communicates with there are 3 environment variables e.g. for the RM case service:

| Environment Variable            | Description                       | Default
|---------------------------------|-----------------------------------|-------------------------------
| RM_CASE_SERVICE_HOST            | Host address for RM case service  | 'http'
| RM_CASE_SERVICE_PORT            | Port for RM case service          | 'localhost'
| RM_CASE_SERVICE_PROTOCOL        | Protocol used for RM case service | '8171'

The services these variables exist for are listed below with the beginnings of their variables and their github links:

| Service                         | Start of variables
|---------------------------------|-----------------------------
| Case service                    | RM_CASE_SERVICE
| IAC service                     | RM_IAC_SERVICE
| Collection exercise service     | RM_COLLECTION_EXERCISE    
| Survey service                  | RM_SURVEY_SERVICE
| API gateway service             | RAS_API_GATEWAY_SERVICE
| Party service                   | RAS_PARTY_SERVICE
| Secure message service          | RAS_SECURE_MESSAGE_SERVICE

The Oauth server is configured slightly differently (This will probably change) these variables are:

