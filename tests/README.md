[![Build Status](https://travis-ci.org/ONSdigital/ras-collection-instrument.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-collection-instrument)


# ras-collection-instrument (Testing)



## Getting started with running and setting up tests with the Collection Instrument Micro Service:

The test folder contains a test_app.py file which is used to specify all unit tests. Above this there is a scripts dir
which contains 3 shell scripts which are explained below. The tests should be run by the developer in the following order:
* Setup Test Environment
* Run Lint checking
* Run BDD Tests
* Run Unit Tests
* Code Coverage
* Check Travis Runs Tests

Once tests can be run manually the code is ready for review.



## Setup Test Environment And Installation

Please ensure you are running this from your virtual environments workspace (e.g. you have run /> workon <my-app>)
From the root folder, install requirements.txt to pull all code and test libraries.

  /> pip install -r requirements.txt

From the root folder, install the requirements_for_test.txt test libraries for code coverage which are not used by the
automated tools or the micro service.

  /> pip install -r requirements_for_test.txt

You can check that you have all required libraries by typing in keywords, hence:

1) BDD Tests type:

  /> behave
  ConfigError: No steps directory in

2) Pylint Tests type:

  /> pylint
  Usage:  pylint [options] module_or_package .... etc

3) Pyunit Tests type:

  /> pytest
  platform linux2 -- Python 2.7.12, pytest-3.0.7, py-1.4.33, pluggy-0.4.0
  rootdir: /home/nherriot/virtalenv/test_collection_instrument, inifile:
  plugins: cov-2.4.0
  collected 0 items / 1 errors

You can find resources to learn more about the test frameworks here: [python behave here.]( http://pythonhosted.org/behave/)



## Running Lint Checker

The pylint checker is used to statistically analyse code for a number of common coding errors and against pep8 standards.
This means that we can have a more automated way of measuring code quality. To run this from the project directory we
need to specify our config file needed to analyse our code. We have modified our checker to not check things like
'line length' since this is pointless with modern screens being so big.

Running pylint from the command line is done with:

  /> pylint --rcfile=.pylint ras-collection-instrument/app.py


## Run BDD Test Cases

This guide describes what to install and how to run the test cases for ONS RAS.


To run all tests, go to the `/tests/behave-BDD-tests` directory and run the command:

	/> behave

The system should output something like:

    ...

    Feature: Handle retrieval of Collection Instrument data # features/get_collection_instrument.feature:1

      @connect_to_database
      Scenario: Get all available collection instrument data              # features/get_collection_instrument.feature:7
        Given one or more collection instruments exist                    # features/steps/steps.py:77 0.002s
        When a request is made for one or more collection instrument data # features/steps/steps.py:151 185.385s
        Then check the returned data are correct                          # features/steps/steps.py:226 0.169s
        And the response status code is 200                               # features/steps/steps.py:209 0.000s

    ...

You can optionally run individual features by running:

    /> behave <http_method_name>_collection_instrument.feature

### Creating BDD Tests

TODO

### Updating Tests

TODO

### Linking Tests to Stories

Each 'scenario' is mapped to a story within confluence contained within:

	https://digitaleq.atlassian.net/wiki/display/RASB/Epics+and+User+Stories+for+Beta

A user story of SDC01 will map to the feature name with the same number code. e.g. SDC01recoverCredentials.feature



## Running Unit Tests

There are several scripts that allow us to run unit tests within this environment. They are contained within /scripts
directory. The 3 shell scripts are:
 * run_linting.sh                   (This runs all linting test cases for the application)
 * run_tests.sh                     (This runs both linting and unit test for the application)
 * run_unit_tests.sh                (This only runs the unit tests for the application)

 The developer should run the lint run_linting.sh shell script first. Once code passes this the developer should move to running the
 run_unit_tests.sh script. Once tests pass for this script the developer can go on to run both together in the shell script run_tests.sh.

### Writing Unit Tests

TODO

### FrameWorks For Unit Tests

TODO



## Code Coverage

There is a code coverage tool used which creates a directory in the root folder called /htmlcov. This contains a break down
of all tests which have been created and analyses what percentage of the code base has been covered. To invoke this tool
form the root folder do:

  /> coverage html

To view % of your code base that is covered by your test cases go to the index file via your browser within the dir:

  /ras-collection-instrument/htmlcov



## Check Travis Runs Tests

The application contains a .travis.yml file. This controls how travis will run the our test scripts. You can see the output
of a particular test run here for this feature as an example:

https://travis-ci.org/ONSdigital/ras-collection-instrument/builds/229137048?utm_source=github_status&utm_medium=notification



