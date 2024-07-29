# ras-frontstage

User interface for Respondent Account Services

## Setup
Based on python 3.11

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

## Run the application
```
make start
```

## Run tests
Install test dependencies with
```bash
pipenv install --dev
```
The Makefile will run the unit and integration tests folder using pytest, and present a coverage report.
These can be easily run via the following commands:
```bash
make test
```
or if you wish to generate an HTML report viewable at htmlcov/index.html
```bash
make test-html
```
or if you are running redis in the docker environment
```bash
make docker-test
```
or if you wish to run a single test file, it can be specified as follows:
```bash
make TESTS=tests/integration/views/surveys/test_surveys_list.py test
```
The syntax above will work equally well with the 'docker-test' target

Note that this script will fail if there is a `node_modules` folder in the repo

## Load the ONS Design System Templates
```
make load-design-system-templates
```

This command will take the version number defined in the `.design-system-version` file and download the templates for that version of the Design System. It will also be automatically run when running `make start`.

To update to a different version of the Design System:
- update the version number in the `.design-system-version` file
- run `make load-design-system-templates` script

## How to run test in pyCharm
* Create a new configuration template in edit configuration. Use `autodetect` option and setup Environment Variable to `APP_SETTINGS=TestingConfig`.

## Configuration
Environment variables available for configuration are listed below:

| Environment Variable            | Description                                         | Default                                         |
|---------------------------------|-----------------------------------------------------|-------------------------------------------------|
| APP_SETTINGS                    | Which config to use                                 | 'Config' (use DevelopmentConfig) for developers |
| SECRET_KEY                      | Secret key used by flask                            | 'ONS_DUMMY_KEY'                                 |
| SECURITY_USER_NAME              | Username for basic auth                             | 'admin'                                         |
| SECURITY_USER_PASSWORD          | Password for basic auth                             | 'secret'                                        |
| JWT_SECRET                      | SECRET used to code JWT                             | 'testsecret'                                    |
| VALIDATE_JWT                    | Boolean for turning on/off JWT validation (True=on) | True                                            |
| GOOGLE_ANALYTICS_MEASUREMENT_ID | Parameter used by google analytics                  | None                                            |
| GOOGLE_TAG_MANAGER_ID           | Parameter used by google tag manager                | None                                            |
| REDIS_HOST                      | Host address for the redis instance                 | 'localhost'                                     |
| REDIS_PORT                      | Port for the redis instance                         | 6379                                            |
| REDIS_DB                        | Database number for the redis instance              | 1                                               |

These are set in [config.py](config.py)

## Updates GNU
* The system now uses GNUPG to encrypt seft messages which is controlled by the saveSeftInGcp flagged stored in the values.yml file
* Due to the version of GNUPG current used in Docker (as of 03/06/2021) (gpg (GnuPG) 2.2.12 libgcrypt 1.8.4) it does NOT
  support an email as a recipient, you need to use the fingerprint
* if you receive a binary public key you MUST convert it to ascii with armor. use the following command.
```
 gpg --export -a <  sdx_preprod_binary_key.gpg > sdx_preprod_binary_key.gpg.asc
```
and load this upto the secret key manager - gnu-public-crypto-key

* to get the fingerprint. the fingerprint will look like 'A8F49D6EE2DE17F03ACF11A9BF16B2EB4DASE991
Also, make sure have an empty local trusted db
```
gpg --with-fingerprint <~/.gnupg/sdx_preprod_binary_key.gpg.asc
```

* It's important to check that the subkey next to the fingerprint has not expired. It is worth sanity checking them on
  the command line

* within the project there is a development public/private gnupg key. However, if you wish to create your own
```
gpg --full-generate-key
gpg --list-secret-keys --keyid-format=long
```
The current values provided are
```
gpg --list-secret-keys --keyid-format=long
------------------------------------
sec   ed25519/3CB9DD17EFF9948B 2021-06-10 [SC]
      C46BB0CB8CEBBC20BC07FCA83CB9DD17EFF9948B
uid                 [ultimate] ONS RAS Dev Team (USE FOR DEVELOPMENT ONLY) <dev@example.com>
ssb   cv25519/ED1B7A3EADF95687 2021-06-10 [E]
```
Then export via
```
gpg --armor --export ED1B7A3EADF95687
```
current saved exported  public private keys are dev-public-key.asc dev-private-key.asc
The private key is only supplied for testing decryption
passphase if needed is PASSWORD1

