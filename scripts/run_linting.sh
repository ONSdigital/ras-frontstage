#!/bin/bash

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

if ! [ -a .build ] ; then
	echo "Creating Virtual Environment"
	virtualenv .build -p python3
fi
source .build/bin/activate

flake8 app/**/*.py --max-complexity 10 --count

display_result $? 1 "Flake 8 code style check"